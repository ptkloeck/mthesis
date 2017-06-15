package main.scala.de.peter_kloeckner.anton_spk

import org.apache.spark.SparkConf
import org.apache.spark.SparkContext
import org.apache.spark.broadcast.Broadcast
import org.apache.spark.rdd.RDD.rddToPairRDDFunctions

object WordCounter {

  def countWords(corpusDir: String, words: Set[String]): collection.Map[String, Int] = {

    val conf = new SparkConf()
      .setAppName("WordCounter")
      .setMaster("local[4]")
    val sc = new SparkContext(conf)

    val lines = sc.textFile(corpusDir + "/*.gz")

    val bWords = sc.broadcast(words)

    val wordCount = lines.flatMap(line => countWords(line, bWords)).reduceByKey((a, b) => a + b)
    val wordToCount = wordCount.collectAsMap()
    sc.stop

    return wordToCount
  }

  def countWords(line: String, bWords: Broadcast[Set[String]]): List[(String, Int)] = {

    var wordCount = List[(String, Int)]()

    val tokens = CorpusParser.getTokens(line)

    for (token <- tokens) {
      if (bWords.value.contains(token))
        wordCount ::= (token, 1)
    }

    wordCount
  }
}