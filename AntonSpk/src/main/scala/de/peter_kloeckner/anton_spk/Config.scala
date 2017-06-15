package main.scala.de.peter_kloeckner.anton_spk

import scala.io.Source
import scala.util.parsing.json.JSON

object Config {

  val configFile = "config.json"
  //val configFile = "config_frink.json"

  // hack to get from the output folder /target/classes to the workspace dir
  val wsPath = getClass().getProtectionDomain().getCodeSource().getLocation().toURI().resolve("..").resolve("..").resolve("..")
  val stream = getClass.getResourceAsStream("/config/" + configFile)
  val source = Source.fromInputStream(stream)
  val lines = try source.mkString finally source.close()
  val json = JSON.parseFull(lines)
  val config = json.get.asInstanceOf[Map[String, Any]]

  def pathToResource(resourceId: String): String = {
    wsPath.resolve(config.get(resourceId).get.asInstanceOf[String]).getPath
  }
}