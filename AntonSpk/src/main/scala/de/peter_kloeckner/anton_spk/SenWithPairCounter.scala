package main.scala.de.peter_kloeckner.anton_spk

import org.apache.spark.SparkConf
import org.apache.spark.SparkContext
import org.apache.spark.broadcast.Broadcast

object SenWithPairCounter {
  
  def numSenWithPair(corpusDir: String, wordPairs: List[(String, String)], posTags: Set[String]) : collection.Map[(String, String), Int] = {
    
    val conf = new SparkConf()
      .setAppName("SenWithPairCounter")
      .setMaster("local[4]")
    val sc = new SparkContext(conf)
    
    val lines = sc.textFile(corpusDir + "/*.gz")
    
    val bWordPairs = sc.broadcast(wordPairs)
    val bPosTags = sc.broadcast(posTags)
    
    val pairCount = lines.flatMap(line => countPairs(line, bPosTags, bWordPairs)).reduceByKey((a, b) => a + b)
    val pairsToCount = pairCount.collectAsMap()
    sc.stop
    
    return pairsToCount
  }
  
  def countPairs(line: String, bPosTags: Broadcast[Set[String]], bWordPairs: Broadcast[List[(String, String)]]) : List[((String, String), Int)] = {

    var pairCount = List[((String, String), Int)]()
    
    val tokens = CorpusParser.getTokensWithPos(line, bPosTags.value).toSet

    for (wordPair <- bWordPairs.value) {

      if (tokens.contains(wordPair._1) && tokens.contains(wordPair._2)) {
        pairCount ::= (wordPair, 1)
      }
    }
    
    return pairCount
  }
}