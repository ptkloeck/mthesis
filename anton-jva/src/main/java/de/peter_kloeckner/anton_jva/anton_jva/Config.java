package de.peter_kloeckner.anton_jva.anton_jva;

import java.io.FileNotFoundException;
import java.io.FileReader;
import java.net.URI;
import java.net.URISyntaxException;

import com.google.gson.JsonIOException;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonSyntaxException;

public class Config {

    private String CONFIG_FILE = "config.json";
    // private String CONFIG_FILE = "config_frink.json";

	private static Config config = new Config();

	public static Config getInstance() {
		return config;
	}

	private JsonObject json;

	public URI wsPath;

	private Config() {
		// hack to get from the output folder /target/classes to the workspace
		// dir
		try {
			wsPath = this.getClass().getProtectionDomain().getCodeSource().getLocation().toURI().resolve("..")
					.resolve("..").resolve("..");
			System.out.println(wsPath);
			json = new JsonParser().parse(new FileReader(wsPath.resolve("config/" + CONFIG_FILE).getPath()))
					.getAsJsonObject();

		} catch (URISyntaxException | JsonIOException | JsonSyntaxException | FileNotFoundException e) {
			e.printStackTrace();
		}
	}

	public String pathToResource(String resourceId) {
		return wsPath.resolve(json.get(resourceId).getAsString()).getPath();
	}
}
