package main.scala.de.peter_kloeckner.anton_spk

object CorpusParser {

  def getTaggedSen(line: String) : String = {
    
    val parts = line.split("\t")
    if (parts.length < 2)
      return ""
      
    parts(1)
  }
  
  def getTokens(line: String):Set[String] = {
    
    val taggedSen = getTaggedSen(line)
    taggedSen.split(" ").toList.flatMap(taggedToken => getToken(taggedToken)).toSet
  }
  
  def getToken(taggedToken: String): List[String] = {
    
    val parts = taggedToken.split("/")
    if (parts.length < 2) {
      return List()
    }
    val token = parts(0)
    List(token)
  }
  
  def getTokensWithPos(line: String, posTags: Set[String]): List[String] = {

    val taggedSen = getTaggedSen(line)
    return taggedSen.split(" ").toList.flatMap(taggedToken => getTokenWithPos(taggedToken, posTags))
  }

  def getTokenWithPos(taggedToken: String, posTags: Set[String]): List[String] = {

    val parts = taggedToken.split("/")
    if (parts.length < 2) {
      return List()
    }
    val token = parts(0)
    val actualPos = parts(1)

    return if (posTags.contains(actualPos)) List(token) else List()
  }
}