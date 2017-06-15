package de.peter_kloeckner.anton_jva.anton_jva;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.PrintWriter;
import java.net.URI;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import javax.xml.stream.XMLStreamException;

import de.tuebingen.uni.sfs.germanet.api.ConRel;
import de.tuebingen.uni.sfs.germanet.api.GermaNet;
import de.tuebingen.uni.sfs.germanet.api.LexRel;
import de.tuebingen.uni.sfs.germanet.api.LexUnit;
import de.tuebingen.uni.sfs.germanet.api.Synset;
import de.tuebingen.uni.sfs.germanet.api.WordCategory;

public class GermaNetQuery {

	private static final int MAX_RELATION_PAIRS = 10000;

	private static final String PURE_RELATION_FILE_SUFFIX = ".txt";

	private static final String ANTONYM_FILE = "antonyms" + PURE_RELATION_FILE_SUFFIX;
	private static final String SYNONYM_FILE = "synonyms" + PURE_RELATION_FILE_SUFFIX;
	private static final String HYPERNYM_FILE = "hyponyms" + PURE_RELATION_FILE_SUFFIX;
	private static final String CO_HYPONYM_FILE = "cohyponyms" + PURE_RELATION_FILE_SUFFIX;
	private static final String MERONYM_FILE = "meronyms" + PURE_RELATION_FILE_SUFFIX;
	private static final String UNRELATED_FILE = "unrelated" + PURE_RELATION_FILE_SUFFIX;

	private static final String ADJ_CREATION_PATH = "/res/de/adj/dataset_creation/";
	private static final String NOUN_CREATION_PATH = "/res/de/noun/dataset_creation/";
	private static final String VERB_CREATION_PATH = "/res/de/verb/dataset_creation/";

	public static void main(String[] args) {

		File gnetDir = new File(Config.getInstance().pathToResource("germanet_dir") + "/GN_V90/GN_V90_XML");

		queryAll(WordCategory.adj, gnetDir);
		// queryAll(WordCategory.nomen, gnetDir);
		// queryAll(WordCategory.verben, gnetDir);
	}

	private static final void queryAll(WordCategory wordCategory, File gnetDir) {

		try {
			GermaNet gnet = new GermaNet(gnetDir);

			System.out.println(gnet.numLexUnits());

			List<Synset> synsets = gnet.getSynsets(wordCategory);
			Collections.shuffle(synsets);

			Set<OrderedWordPair> allPairs = new HashSet<OrderedWordPair>();

			Set<OrderedWordPair> antonyms = new HashSet<OrderedWordPair>();
			Set<OrderedWordPair> synonyms = new HashSet<OrderedWordPair>();
			Set<OrderedWordPair> hypernyms = new HashSet<OrderedWordPair>();
			Set<OrderedWordPair> cohyponyms = new HashSet<OrderedWordPair>();
			Set<OrderedWordPair> meronyms = new HashSet<OrderedWordPair>();
			Set<OrderedWordPair> unrels = new HashSet<OrderedWordPair>();

			for (Synset synset : synsets) {

				List<ConRel> hypernymConRels = new ArrayList<ConRel>();
				hypernymConRels.add(ConRel.has_hypernym);
				queryFromDoubleSynset(synset, hypernymConRels, hypernyms);

				List<ConRel> meronymConRels = new ArrayList<ConRel>();
				meronymConRels.add(ConRel.has_component_meronym);
				meronymConRels.add(ConRel.has_member_meronym);
				meronymConRels.add(ConRel.has_portion_meronym);
				meronymConRels.add(ConRel.has_substance_meronym);
				queryFromDoubleSynset(synset, meronymConRels, meronyms);

				queryFromSingleSynset(synset, LexRel.has_antonym, antonyms);
				queryFromSingleSynset(synset, LexRel.has_synonym, synonyms);

				queryCoHyponyms(synset, cohyponyms);
			}

			queryUnrelated(unrels);

			String creationPath = "";
			switch (wordCategory) {
			case adj:
				creationPath = ADJ_CREATION_PATH;
				break;
			case nomen:
				creationPath = NOUN_CREATION_PATH;
				break;
			case verben:
				creationPath = VERB_CREATION_PATH;
				break;
			default:
				break;
			}
			writePairs(antonyms, creationPath + ANTONYM_FILE);
			writePairs(synonyms, creationPath + SYNONYM_FILE);
			writePairs(hypernyms, creationPath + HYPERNYM_FILE);
			writePairs(cohyponyms, creationPath + CO_HYPONYM_FILE);
			writePairs(meronyms, creationPath + MERONYM_FILE);
			writePairs(unrels, creationPath + UNRELATED_FILE);

		} catch (XMLStreamException | IOException e) {
			e.printStackTrace();
			System.out.println("Could not load GermaNet");
		}
	}

	private static void queryFromSingleSynset(Synset synset, LexRel lexRel, Set<OrderedWordPair> pairs) {

		List<LexUnit> lexUnits = synset.getLexUnits();
		for (LexUnit lexUnit : lexUnits) {
			List<LexUnit> otherLexUnits = lexUnit.getRelatedLexUnits(lexRel);
			for (LexUnit otherLexUnit : otherLexUnits) {
				pairs.add(new OrderedWordPair(lexUnit.getOrthForm(), otherLexUnit.getOrthForm()));
			}
		}
	}

	private static void queryFromDoubleSynset(Synset synset, List<ConRel> conRels, Set<OrderedWordPair> pairs) {

		List<LexUnit> lexUnits = synset.getLexUnits();

		List<Synset> relatedSynsets = new ArrayList<Synset>();
		for (ConRel conRel : conRels) {
			relatedSynsets.addAll(synset.getRelatedSynsets(conRel));
		}

		for (LexUnit lexUnit : lexUnits) {

			for (Synset hypernymSynset : relatedSynsets) {
				for (LexUnit otherLexUnit : hypernymSynset.getLexUnits()) {
					pairs.add(new OrderedWordPair(lexUnit.getOrthForm(), otherLexUnit.getOrthForm()));
				}
			}
		}
	}

	private static void queryCoHyponyms(Synset synset, Set<OrderedWordPair> coHyponyms) {

		List<LexUnit> lexUnits = synset.getLexUnits();

		for (Synset parentSynset : synset.getRelatedSynsets(ConRel.has_hypernym)) {

			for (Synset coHyponymSynset : parentSynset.getRelatedSynsets(ConRel.has_hyponym)) {

				if (!synset.equals(coHyponymSynset)) {

					for (LexUnit lexUnit : lexUnits) {
						for (LexUnit otherLexUnit : coHyponymSynset.getLexUnits()) {
							coHyponyms.add(new OrderedWordPair(lexUnit.getOrthForm(), otherLexUnit.getOrthForm()));
						}
					}
				}
			}
		}
	}

	private static void queryUnrelated(Set<OrderedWordPair> unrels) {
		
	}

	private static void writePairs(Set<OrderedWordPair> pairs, String filePath) {

		try {
			PrintWriter writer = new PrintWriter(Config.getInstance().wsPath.getPath() + filePath);

			for (OrderedWordPair pair : pairs) {
				writer.println(pair.word1 + " " + pair.word2);
			}
			writer.close();

		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
	}

	private static class OrderedWordPair {

		private String word1;
		private String word2;

		public OrderedWordPair(String word1, String word2) {
			if (word1.compareTo(word2) <= 0) {
				this.word1 = word1;
				this.word2 = word2;
			} else {
				this.word1 = word2;
				this.word2 = word1;
			}
		}

		@Override
		public int hashCode() {
			final int prime = 31;
			int result = 1;
			result = prime * result + ((word1 == null) ? 0 : word1.hashCode());
			result = prime * result + ((word2 == null) ? 0 : word2.hashCode());
			return result;
		}

		@Override
		public boolean equals(Object obj) {
			if (this == obj)
				return true;
			if (obj == null)
				return false;
			if (getClass() != obj.getClass())
				return false;
			OrderedWordPair other = (OrderedWordPair) obj;
			if (word1 == null) {
				if (other.word1 != null)
					return false;
			} else if (!word1.equals(other.word1))
				return false;
			if (word2 == null) {
				if (other.word2 != null)
					return false;
			} else if (!word2.equals(other.word2))
				return false;
			return true;
		}
	}
}
