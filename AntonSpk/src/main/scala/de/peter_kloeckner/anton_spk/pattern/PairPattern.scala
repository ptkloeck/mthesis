package main.scala.de.peter_kloeckner.anton_spk.pattern

class PairPattern(val pairRegex: String) extends java.io.Serializable with Equals {

  val pattern = pairRegex.r
  val tokenPosPairs = pairRegex.split(" ").filter(x => !x.contains(PatternExtractor.TokenRegex)).toSet

  def checkSentence(taggedSen: String, senTokenPosPairs : Set[String]): List[(String, String)] = {

    var foundPairs = List[(String, String)]()

    if (tokenPosPairs.subsetOf(senTokenPosPairs)) {
      pattern.findFirstMatchIn(taggedSen) match {
        case Some(m) => {
          val word1 = m.group(1)
          val word2 = m.group(2)

          val foundPair = if (word1 < word2) (word1, word2) else (word2, word1)
          foundPairs ::= foundPair
        }
        case None =>
      }
    }

    return foundPairs
  }

  def canEqual(other: Any) = {
    other.isInstanceOf[PairPattern]
  }

  override def equals(other: Any) = {
    other match {
      case that: PairPattern => that.canEqual(PairPattern.this) && pairRegex == that.pairRegex
      case _ => false
    }
  }

  override def hashCode() = {
    val prime = 41
    prime + pairRegex.hashCode
  }
}