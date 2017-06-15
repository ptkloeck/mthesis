package main.scala.de.peter_kloeckner.anton_spk.pattern

import org.apache.spark.SparkConf
import org.apache.spark.SparkContext
import org.apache.spark.broadcast.Broadcast
import scala.collection.mutable.LinkedHashMap
import main.scala.de.peter_kloeckner.anton_spk.CorpusParser
import main.scala.de.peter_kloeckner.anton_spk.Util
import org.apache.spark.rdd.RDD.rddToPairRDDFunctions

object PatternFeatureExtractor {

  def extractFeatures(corpusDir: String, patternToCount: LinkedHashMap[PairPattern, Int], pairToCount: collection.Map[(String, String), Int]): collection.Map[(String, String), Map[PairPattern, Float]] = {

    val conf = new SparkConf()
      .setAppName("PatternFeatureExtractor")
      .setMaster("local[4]")
    val sc = new SparkContext(conf)

    val lines = sc.textFile(corpusDir + "/*.gz")

    val bPatternToCount = sc.broadcast(patternToCount)
    val bPairToCount = sc.broadcast(pairToCount)
    val bNumSen = sc.broadcast(lines.count().toInt)

    val pairToPatternToCount = lines.flatMap(line => countPatterns(line, bPatternToCount, bPairToCount))
      .reduceByKey((patternToCount1, patternToCount2) => patternToCount1 ++ patternToCount2.map { case (pattern, count) => pattern -> (count + patternToCount1.getOrElse(pattern, 0)) })
      .map(pairPatternToCount => computePatternsScore(pairPatternToCount, bPatternToCount, bPairToCount, bNumSen))
      .collectAsMap()
      
    sc.stop
    
    pairToPatternToCount
  }

  def countPatterns(line: String, bPatternToCount: Broadcast[LinkedHashMap[PairPattern, Int]], bPairToCount: Broadcast[collection.Map[(String, String), Int]]): List[((String, String), Map[PairPattern, Int])] = {

    var pairPatternCount = List[((String, String), Map[PairPattern, Int])]()

    val taggedSen = CorpusParser.getTaggedSen(line)
    if (taggedSen == "") {
      return pairPatternCount
    }
    val senTokenPosPairs = taggedSen.split(" ").toSet
    
    for (pattern <- bPatternToCount.value.keySet) {

      val foundPairs = pattern.checkSentence(taggedSen, senTokenPosPairs)

      for (foundPair <- foundPairs) {

        val pairToCount = bPairToCount.value
        
        if (pairToCount.contains(foundPair)) {
          pairPatternCount ::= (foundPair, Map(pattern -> 1))
        }
      }
    }

    return pairPatternCount
  }

  def computePatternsScore(pairPatternToCount: ((String, String), Map[PairPattern, Int]), bPatternToCount: Broadcast[LinkedHashMap[PairPattern, Int]], bPairToCount: Broadcast[collection.Map[(String, String), Int]], bNumSen: Broadcast[Int]): ((String, String), Map[PairPattern, Float]) = {

    val pair = pairPatternToCount._1
    val patternToCount = pairPatternToCount._2
    
    val pairCount = bPairToCount.value.get(pair).getOrElse(0)

    val patternToScore = patternToCount map {
      case (pattern, pairPatternCount) => {
        
        val patternCount = bPatternToCount.value.get(pattern).getOrElse(0)
        val score = Util.lmi(patternCount, pairCount, pairPatternCount, bNumSen.value)
        
        (pattern -> score)
      }
    }

    (pair, patternToScore)
  }
}