df = read.csv(file = "../res/adj/data_ant_syn_adj.tsv", sep="\t")

# make rel_class human-readable for plot
df_we <- df["rel_class"]
df_we$rel_class[df_we$rel_class==1] = "Antonyms"
df_we$rel_class[df_we$rel_class==2] = "Synonyms"

df_we["word_embed_sim"] <- df["word_embed_sim"]

library(ggplot2)

p <- ggplot(df_we, aes(x=word_embed_sim, fill=rel_class)) +
  geom_histogram(position="dodge") + scale_fill_discrete(name="Relation")

print(p)