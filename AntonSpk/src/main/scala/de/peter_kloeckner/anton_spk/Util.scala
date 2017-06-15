package main.scala.de.peter_kloeckner.anton_spk

object Util {
  
  def lmi(freqA: Int, freqB: Int, jointFreq: Int, total: Int): Float = {

    if (freqA == 0 || freqB == 0 || jointFreq == 0 || total == 0) {
      Float.MinValue
    } else {
      jointFreq * Math.log((total * jointFreq) / (freqA * freqB.toFloat)).toFloat
    }
  }
}