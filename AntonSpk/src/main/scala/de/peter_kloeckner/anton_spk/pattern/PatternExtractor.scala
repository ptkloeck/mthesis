package main.scala.de.peter_kloeckner.anton_spk.pattern

import org.apache.spark.SparkConf
import org.apache.spark.SparkContext
import org.apache.spark.broadcast.Broadcast
import scala.util.matching.Regex
import main.scala.de.peter_kloeckner.anton_spk.CorpusParser
import org.apache.spark.rdd.RDD.rddToPairRDDFunctions

object PatternExtractor {

  val TokenRegex = "(\\w+)"
  val TokenPosRegex = "[^\\s]+"
  val WsTokenPosRegex = "\\s" + TokenPosRegex
  val TokenPosWsRegex = TokenPosRegex + "\\s"
  val BetweenAntsRegex = "(" + WsTokenPosRegex + "){1,4}\\s"

  def extractAntPatterns(corpusDir: String, antPairs: List[(String, String)], posTags: Set[String], posCategory: String) = {

    val conf = new SparkConf()
      .setAppName("PatternExtractor")
      .setMaster("local[4]")
    val sc = new SparkContext(conf)

    val bPairsToRegexes = sc.broadcast(createRegexes(posTags, antPairs))
    val bAntPairs = sc.broadcast(antPairs)
    val bPosTags = sc.broadcast(posTags)

    val lines = sc.textFile(corpusDir + "/*.gz")

    lines.flatMap(line => findAntPair(line, bPosTags, bAntPairs))
      .flatMap(enhancedLine => extractPatterns(enhancedLine, bPairsToRegexes))
      .reduceByKey((a, b) => a + b)
      .map(a => a._1 + "\t" + a._2)
      .saveAsTextFile(posCategory + "_patterns")

    sc.stop
  }

  def createRegexes(posTags: Set[String], antPairs: List[(String, String)]): Map[String, List[Regex]] = {

    var pairsToRegexes: Map[String, List[Regex]] = Map()

    var posTagRegex = "("
    for (posTag <- posTags.dropRight(1)) {
      posTagRegex += posTag + "|"
    }
    posTagRegex += posTags.last + ")"

    for (antPair <- antPairs) {
      val ant1 = antPair._1
      val ant2 = antPair._2

      val ant1Regex = "(" + ant1 + ")" + "/" + posTagRegex
      val ant2Regex = "(" + ant2 + ")" + "/" + posTagRegex

      val baseRegex = ant1Regex + BetweenAntsRegex + ant2Regex
      val invBaseRegex = ant2Regex + BetweenAntsRegex + ant1Regex
      var regexes: List[Regex] = List()

      for (i <- 0 to 3) {
        for (j <- 0 to 3) {

          val leftRegex = TokenPosWsRegex * i
          val rightRegex = WsTokenPosRegex * j
          val regex = leftRegex + baseRegex + rightRegex
          regexes +:= regex.r

          val invRegex = leftRegex + invBaseRegex + rightRegex
          regexes +:= invRegex.r
        }
      }

      pairsToRegexes += (ant1 + " " + ant2 -> regexes)
    }

    return pairsToRegexes
  }

  def findAntPair(line: String, bPosTags: Broadcast[Set[String]], bAntPairs: Broadcast[List[(String, String)]]): List[(String, String)] = {

    var linesWithPair: List[(String, String)] = List()
    
    val parts = line.split("\t")
    if (parts.length < 2)
      return linesWithPair
    val taggedSen = line.split("\t")(1)
    val tokens = CorpusParser.getTokensWithPos(line, bPosTags.value).toSet

    for (antPair <- bAntPairs.value) {

      if (tokens.contains(antPair._1) && tokens.contains(antPair._2)) {
        linesWithPair +:= (taggedSen, antPair._1 + " " + antPair._2)
      }
    }

    return linesWithPair
  }

  def extractPatterns(enhancedLine: (String, String), bPairsToRegexes: Broadcast[Map[String, List[Regex]]]): List[(String, Int)] = {

    val taggedSen = enhancedLine._1
    val antPair = enhancedLine._2

    var patterns: List[(String, Int)] = List()
    val regexes = bPairsToRegexes.value.get(antPair)

    for (regex <- regexes.getOrElse(List())) {

      for (matched <- regex.findAllIn(taggedSen).matchData) {

        val startPattern = matched.start(0)
        val startAnt1 = matched.start(1)
        val endAnt1 = matched.end(1)
        val startAnt2 = matched.start(4)
        val endAnt2 = matched.end(4)
        val endPattern = matched.end(0)
        val pattern = taggedSen.substring(startPattern, startAnt1) + TokenRegex + taggedSen.substring(endAnt1, startAnt2) + TokenRegex + taggedSen.substring(endAnt2, endPattern)
        patterns +:= (pattern, 1)
      }
    }
    return patterns
  }
}