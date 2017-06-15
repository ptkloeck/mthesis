package main.scala.de.peter_kloeckner.anton_spk.pattern

import org.apache.spark.SparkConf
import org.apache.spark.SparkContext
import org.apache.spark.broadcast.Broadcast
import org.apache.spark.rdd.RDD.rddToPairRDDFunctions
import java.io.PrintWriter
import java.io.File
import main.scala.de.peter_kloeckner.anton_spk.CorpusParser
import main.scala.de.peter_kloeckner.anton_spk.Util
import scala.Ordering

object PatternRanker {

  val OutFileSuffix = "_pattern_ranking.txt"

  def rankPatterns(corpusDir: String, patterns: List[String], antPairs: List[(String, String)], numSenWithAntPair: Int, posCategory: String) = {

    val conf = new SparkConf()
      .setAppName("PatternRanker")
      .setMaster("local[4]")
    val sc = new SparkContext(conf)

    val lines = sc.textFile(corpusDir + "/*.gz")

    val bPairPatterns = sc.broadcast(compilePairPatterns(patterns))
    val bAntPairs = sc.broadcast(combinePairs(antPairs))
    val bNumSen = sc.broadcast(lines.count().toInt)
    val bNumSenWithAntPair = sc.broadcast(numSenWithAntPair)

    val topPatterns: Array[(String, (Int, Int, Float))] = lines.flatMap(line => checkPatterns(line, bPairPatterns, bAntPairs))
      .reduceByKey((a, b) => (a._1 + b._1, a._2 + b._2)).map(a => computePatternScore(a, bNumSen, bNumSenWithAntPair)).collect()

    //.top(10000)(Ordering[Float].on(a => a._2._3))

    val writer = new PrintWriter(new File(posCategory + OutFileSuffix))
    for (pattern <- topPatterns) {
      val line = pattern._1 + "\t" + pattern._2._1 + "\t" + pattern._2._2 + "\t" + pattern._2._3
      println(line)
      writer.println(line)
    }
    writer.close()
    sc.stop
  }

  def compilePairPatterns(patterns: List[String]): List[PairPattern] = {

    var pairPatterns = List[PairPattern]()
    for (pattern <- patterns) {
      try {
        val pairPattern = new PairPattern(pattern)
        pairPatterns ::= pairPattern

      } catch {
        case e: java.util.regex.PatternSyntaxException =>
      }
    }
    return pairPatterns
  }

  def combinePairs(pairs: List[(String, String)]): Set[String] = {

    var combinedPairs: Set[String] = Set[String]()

    for (pair <- pairs) {

      val word1 = pair._1
      val word2 = pair._2

      val combinedPair = if (word1 < word2) word1 + " " + word2 else word2 + " " + word1
      combinedPairs += combinedPair
    }

    return combinedPairs
  }

  def combinePair(pair: (String, String)): String = {
    val word1 = pair._1
    val word2 = pair._2
    if (word1 < word2) word1 + " " + word2 else word2 + " " + word1
  }

  def checkPatterns(line: String, bPairPatterns: Broadcast[List[PairPattern]], bAntPairs: Broadcast[Set[String]]): List[(String, (Int, Int))] = {

    var counts = List[(String, (Int, Int))]()

    val taggedSen = CorpusParser.getTaggedSen(line)
    if (taggedSen == "") {
      return counts
    }
    val senTokenPosPairs = taggedSen.split(" ").toSet

    for (pairPattern <- bPairPatterns.value) {

      for (foundPair <- pairPattern.checkSentence(taggedSen, senTokenPosPairs)) {
        val antPair = bAntPairs.value.contains(combinePair(foundPair))
        counts +:= (pairPattern.pairRegex, (if (antPair) 1 else 0, if (antPair) 0 else 1))
      }
    }

    return counts
  }

  def computePatternScore(patternCount: (String, (Int, Int)), bNumSen: Broadcast[Int], bNumSenWithAntPair: Broadcast[Int]): (String, (Int, Int, Float)) = {

    val jointFreq = patternCount._2._1
    val freqA = bNumSenWithAntPair.value
    val freqB = jointFreq + patternCount._2._2
    val total = bNumSen.value

    val lmi = Util.lmi(freqA, freqB, jointFreq, total)

    (patternCount._1, (patternCount._2._1, patternCount._2._2, lmi))
  }
}