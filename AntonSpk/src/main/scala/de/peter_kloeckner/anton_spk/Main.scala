package main.scala.de.peter_kloeckner.anton_spk

import java.io.File
import java.io.PrintWriter
import java.nio.file.Files
import java.nio.file.Paths

import scala.collection.mutable.LinkedHashMap
import scala.io.Source

import main.scala.de.peter_kloeckner.anton_spk.pattern.PairPattern
import main.scala.de.peter_kloeckner.anton_spk.pattern.PatternExtractor
import main.scala.de.peter_kloeckner.anton_spk.pattern.PatternFeatureExtractor
import main.scala.de.peter_kloeckner.anton_spk.pattern.PatternRanker

object Main {

  val MinAntPairPatternFreq = 10
  val PosCategoryAdj = "adj"
  val PosCategoryNoun = "noun"
  val PosCategoryVerb = "verb"
  val PosTagsAdj = Set("JJ")
  val PosTagsNoun = Set("NN", "NNS", "NNP", "NNPS")
  val PosTagsVerb = Set("VB", "VBD", "VBG", "VBN", "VBP", "VBZ")

  def main(args: Array[String]) = {

    //val patterns = readExtractedPatterns(PosCategoryAdj + "_patterns", MinAntPairPatternFreq)
    //print(patterns.length)
    //countWords(Config.pathToResource("google_most_freq_words"))

    //extractAdjAntPatterns()
    //scoreAdjAntPatterns()

    //extractNounAntPatterns()
    //scoreNounAntPatterns()

    //extractVerbAntPatterns()
    //scoreVerbAntPatterns()

    //extractPatternFeaturesWnDataset()

    //extractPatternFeaturesResId("turn_testset")
    //extractPatternFeaturesResId("lzqz_testset")
    extractPatternFeaturesResId("gre_testset")

    //val exc = "/home/peter/anaconda3/bin/python " + Config.wsPath.getPath() + "AntonPython/anton/visualize/visu.py" !
  }

  def extractPatternFeaturesWnDataset() = {

    extractPatternFeaturesResId("adj_ants")
    extractPatternFeaturesResId("adj_ants_all")
    extractPatternFeaturesResId("noun_ants")
    extractPatternFeaturesResId("noun_ants_all")
    extractPatternFeaturesResId("verb_ants")
    extractPatternFeaturesResId("verb_ants_all")
  }

  def extractPatternFeaturesResId(resId: String) = {
    var data_path = Config.pathToResource(resId).replace(".tsv", "_adj.tsv")
    if (Files.exists(Paths.get(data_path))) {
      extractPatternFeatures(Config.pathToResource("corpus_dir"), PosCategoryAdj, PosTagsAdj, data_path)
    }
    data_path = Config.pathToResource(resId).replace(".tsv", "_noun.tsv")
    if (Files.exists(Paths.get(data_path))) {
      extractPatternFeatures(Config.pathToResource("corpus_dir"), PosCategoryNoun, PosTagsNoun, data_path)
    }
    data_path = Config.pathToResource(resId).replace(".tsv", "_verb.tsv")
    if (Files.exists(Paths.get(data_path))) {
      extractPatternFeatures(Config.pathToResource("corpus_dir"), PosCategoryVerb, PosTagsVerb, data_path)
    }
  }

  def countWords(file: String) = {

    var words = List[String]()

    val lines = Source.fromFile(file).getLines()
    for (line <- lines) {
      words ::= line.trim()
    }

    val wordToCount = WordCounter.countWords(Config.pathToResource("corpus_dir"), words.toSet)

    val writer = new PrintWriter(new File(file.replace(".txt", ".tsv")))
    writer.println("\t" + "freq")
    wordToCount.foreach { case (word, count) => writer.println(word + "\t" + count) }
    writer.close()
  }

  def extractPatterns(pairResourceId: String, posTags: Set[String], posCategory: String) = {

    val antPairs = readAntPairs(Config.pathToResource(pairResourceId))
    PatternExtractor.extractAntPatterns(Config.pathToResource("corpus_dir"), antPairs, posTags, posCategory)
  }

  def extractAdjAntPatterns() = {
    extractPatterns("adj_ants", PosTagsAdj, PosCategoryAdj)
  }

  def extractNounAntPatterns() = {
    extractPatterns("noun_ants", PosTagsNoun, PosCategoryNoun)
  }

  def extractVerbAntPatterns() = {
    extractPatterns("verb_ants", PosTagsVerb, PosCategoryVerb)
  }

  def scoreAntPatterns(pairResourceId: String, posCategory: String, posTags: Set[String]) = {

    val antPairs = readAntPairs(Config.pathToResource(pairResourceId))
    val patterns = readExtractedPatterns(posCategory + "_patterns", MinAntPairPatternFreq)

    val pairCount = SenWithPairCounter.numSenWithPair(Config.pathToResource("corpus_dir"), antPairs, posTags)
    val numSenWithPair = pairCount.foldLeft(0)((a, b) => a + b._2)

    PatternRanker.rankPatterns(Config.pathToResource("corpus_dir"), patterns, antPairs, numSenWithPair, posCategory)
  }

  def scoreAdjAntPatterns() = {
    scoreAntPatterns("adj_ants", PosCategoryAdj, PosTagsAdj)
  }

  def scoreNounAntPatterns() = {
    scoreAntPatterns("noun_ants", PosCategoryNoun, PosTagsNoun)
  }

  def scoreVerbAntPatterns() = {
    scoreAntPatterns("verb_ants", PosCategoryVerb, PosTagsVerb)
  }

  def extractPatternFeatures(corpusDir: String, posCategory: String, posTags: Set[String], dataPath: String) = {

    val pairs = readPairs(dataPath)
    val pairToCount = SenWithPairCounter.numSenWithPair(Config.pathToResource("corpus_dir"), pairs, posTags)
    val patternToCount = readRankedPatterns(posCategory + PatternRanker.OutFileSuffix)

    val pairToPatternToScore = PatternFeatureExtractor.extractFeatures(corpusDir, patternToCount, pairToCount)

    val source = Source.fromFile(dataPath)
    val lines = try Source.fromFile(dataPath).getLines.toList finally source.close()

    new File(dataPath).delete()

    val writer = new PrintWriter(new File(dataPath))
    writer.println(lines(0) + (1 to patternToCount.size).toList.foldLeft("")((a, b) => a + "\t" + "bestPattern" + b))
    var i = 1
    for (pair <- pairs) {
      var line = lines(i)
      val patternToScore = pairToPatternToScore.get(pair).getOrElse(Map())
      for (pattern <- patternToCount.keys) {
        val score = patternToScore.get(pattern).getOrElse(0.0f)
        line += "\t" + score
      }
      writer.println(line)
      i += 1
    }
    writer.close()
  }

  /**
   * assumes that there is a column named rel_class in the tsv pair data whose value is 1 if the pair is an antonym pair
   *
   * @param pairFile
   * @return
   */
  def readAntPairs(pairFile: String): List[(String, String)] = {

    var antPairs: List[(String, String)] = List()

    val lines = Source.fromFile(pairFile).getLines()

    val relationClassColumn = lines.next.split("\t").indexOf("rel_class")

    for (line <- lines) {
      val parts = line.split("\t")
      val combinedPair = parts(0)
      if (parts(relationClassColumn) == 1.toString()) {
        val words = combinedPair.split(" ")
        val antPair = if (words(0) < words(1)) (words(0), words(1)) else (words(1), words(0))
        antPairs ::= antPair
      }
    }

    return antPairs
  }

  def readPairs(pairFile: String): List[(String, String)] = {

    var pairs: List[(String, String)] = List()

    val lines = Source.fromFile(pairFile).getLines().drop(1)

    for (line <- lines) {
      val antonyms = line.split("\t")(0)
      val words = antonyms.split(" ")
      val pair = if (words(0) < words(1)) (words(0), words(1)) else (words(1), words(0))

      pairs :+= pair
    }

    return pairs
  }

  def readExtractedPatterns(path: String, minOccurance: Int = 0): List[String] = {

    var patterns = List[String]()
    for (file <- new java.io.File(path).listFiles.filter(_.getName.startsWith("part"))) {

      val lines = Source.fromFile(file).getLines().drop(1)

      for (line <- lines) {

        val parts = line.split("\t")
        val pattern = parts(0)
        val occurence = parts(1).toInt
        if (occurence >= minOccurance) {
          patterns :+= line.split("\t")(0)
        }
      }
    }

    patterns
  }

  def readRankedPatterns(path: String): LinkedHashMap[PairPattern, Int] = {

    val lines = Source.fromFile(path).getLines()

    var patternToCount = LinkedHashMap[PairPattern, Int]()

    for (line <- lines) {

      val parts = line.split("\t")
      patternToCount += (new PairPattern(parts(0)) -> (parts(1).toInt + parts(2).toInt))
    }

    return patternToCount
  }
}