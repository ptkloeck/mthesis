
makeCoocPlot <- function(df, column_name, title, make_legend, x_axis_name, compute_lmi, bins) {
  
  # make rel_class human-readable for plot
  df_cooc <- df["rel_class"]
  df_cooc$rel_class[df_cooc$rel_class==1] = "Antonyms"
  df_cooc$rel_class[df_cooc$rel_class==2] = "Synonyms"
  
  # extract coocurrence counts
  df_cooc[column_name] <- df[column_name]
  
  if(compute_lmi) {
    df_cooc[column_name] <- df[column_name] * log(105000000 * df[column_name] / (df["freq1"] + df["freq2"]))
  } else {
    df_cooc[df_cooc == 0] = NaN
  }
  
  # shift right to bring the data in the interval [1, x] to get positive log values
  df_cooc[column_name] <- df_cooc[column_name] + abs(min(df_cooc[column_name], na.rm = TRUE)) + 1
  df_cooc[column_name] <- log(df_cooc[column_name])
  
  # map non existent association scores to 0
  df_cooc[is.na(df_cooc)] <- 0
  
  p <- ggplot(df_cooc, aes(x=both_cooc_lmi, fill=rel_class)) +
    geom_histogram(position="dodge", bins=bins) + 
    scale_fill_discrete(name="Relation") + 
    labs(x = x_axis_name) +
    ggtitle(title)
  
  if(make_legend) {
    p <- p + scale_fill_discrete(name="Relation") 
  }
  
  return(p)
}

comparativeCoocPlot <- function(column_name, x_axis_name, compute_lmi, bins) {
  
  library(ggplot2)
  
  theme_set(theme_gray(base_size = 16))
  
  library(cowplot)
  
  df_adj = read.csv(file = "../res/adj/data_ant_syn_adj.tsv", sep="\t")
  df_noun = read.csv(file = "../res/noun/data_ant_syn_noun.tsv", sep="\t")
  df_verb = read.csv(file = "../res/verb/data_ant_syn_verb.tsv", sep="\t")
  
  p1 = makeCoocPlot(df_adj, column_name, "Adjectives", TRUE, x_axis_name, compute_lmi, bins)
  p2 = makeCoocPlot(df_noun, column_name, "Nouns", FALSE, x_axis_name, compute_lmi, bins)
  p3 = makeCoocPlot(df_verb, column_name, "Verbs", FALSE, x_axis_name, compute_lmi, bins)
  
  grobs <- ggplotGrob(p1)$grobs
  legend <- grobs[[which(sapply(grobs, function(x) x$name) == "guide-box")]]
  
  p = plot_grid(p1 + theme(legend.position="none"), p2 + theme(legend.position="none")
                , p3 + theme(legend.position="none"), legend, ncol = 2, nrow = 2)
  
  print(p)
}

#comparativeCoocPlot("in_para_cooc", "log(para_cooc)", TRUE, 30)
#comparativeCoocPlot("in_sen_cooc", "log(sen_cooc)", TRUE, 30)
comparativeCoocPlot("both_cooc_lmi", "log(both_cooc)", FALSE, 10)