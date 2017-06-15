df_adj = read.csv(file = "../res/adj/data_ant_syn_adj.tsv", sep="\t")
df_noun = read.csv(file = "../res/noun/data_ant_syn_noun.tsv", sep="\t")
df_verb = read.csv(file = "../res/verb/data_ant_syn_verb.tsv", sep="\t")

library(ggplot2)

theme_set(theme_gray(base_size = 16))

library(cowplot)

makeJbPlot <- function(df, title, make_legend) {
  
  num_top1_ant = nrow(df[df$top1_sim_fs==1 & df$rel_class==1,])
  num_top1_syn = nrow(df[df$top1_sim_fs==1 & df$rel_class==2,])
  
  top_jb_sim = rep("top01", num_top1_ant + num_top1_syn)
  relation = c(rep("Antonyms", num_top1_ant), rep("Synonyms", num_top1_syn))
  
  num_top3_ant = nrow(df[df$top3_sim_fs==1 & df$rel_class==1,])
  num_top3_syn = nrow(df[df$top3_sim_fs==1 & df$rel_class==2,]) 
  
  top_jb_sim = c(top_jb_sim, rep("top03", num_top3_ant + num_top3_syn))
  relation = c(relation, c(rep("Antonyms", num_top3_ant), rep("Synonyms", num_top3_syn)))
  
  num_top5_ant = nrow(df[df$top5_sim_fs==1 & df$rel_class==1,])
  num_top5_syn = nrow(df[df$top5_sim_fs==1 & df$rel_class==2,]) 
  
  top_jb_sim = c(top_jb_sim, rep("top05", num_top5_ant + num_top5_syn))
  relation = c(relation, c(rep("Antonyms", num_top5_ant), rep("Synonyms", num_top5_syn)))
  
  num_top10_ant = nrow(df[df$top10_sim_fs==1 & df$rel_class==1,])
  num_top10_syn = nrow(df[df$top10_sim_fs==1 & df$rel_class==2,]) 
  
  top_jb_sim = c(top_jb_sim, rep("top10", num_top10_ant + num_top10_syn))
  relation = c(relation, c(rep("Antonyms", num_top10_ant), rep("Synonyms", num_top10_syn)))
  
  num_top20_ant = nrow(df[df$top20_sim_fs==1 & df$rel_class==1,])
  num_top20_syn = nrow(df[df$top20_sim_fs==1 & df$rel_class==2,]) 
  
  top_jb_sim = c(top_jb_sim, rep("top20", num_top20_ant + num_top20_syn))
  relation = c(relation, c(rep("Antonyms", num_top20_ant), rep("Synonyms", num_top20_syn)))
  
  df_jb = data.frame(top_jb_sim, relation)
  
  p <- ggplot(data=df_jb, aes(x=top_jb_sim, fill=relation)) +
    geom_bar(stat="count", position=position_dodge()) +
    ggtitle(title)
  
  if(make_legend) {
    p <- p + scale_fill_discrete(name="Relation") 
  }
  
  return(p)
}

p1 = makeJbPlot(df_adj, "Adjectives", TRUE)
p2 = makeJbPlot(df_noun, "Nouns", FALSE)
p3 = makeJbPlot(df_verb, "Verbs", FALSE)

grobs <- ggplotGrob(p1)$grobs
legend <- grobs[[which(sapply(grobs, function(x) x$name) == "guide-box")]]

p = plot_grid(p1 + theme(legend.position="none"), p2 + theme(legend.position="none")
              , p3 + theme(legend.position="none"), legend, ncol = 2, nrow = 2)

print(p)
