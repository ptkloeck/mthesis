DEPENDENCIES

python dependencies:

(anaconda python 3.4 comes with the following:)
-scikit
-nltk

additional dependencies
-gensim
-pyhyphen
-python-levenshtein
-seaborn (for plots)

You most probably can make the python project running with (a maybe slightly altered version of) the
following commands:

wget http://repo.continuum.io/archive/Anaconda3-4.0.0-Linux-x86_64.sh
bash Anaconda3-4.0.0-Linux-x86_64.sh
conda install -c anaconda gensim=0.12.4
pip install pyhyphen
pip install python-levenshtein
conda install seaborn

java/scala dependencies:

The java and scala projects are maven projects, so only maven and java has to be installed.



RUN PROJECT

The input of the system is a file (xx.tsv) in tsv format. The first column should contain the word pairs. A word pair should consist of two words ordered alphabetically and separated by a space. The column "pos_tag" has to contain the pos tag category (either noun, adj or verb). In case the system should be evaluated a second column "rel_class" should contain the relation of the two words (either 1 for antonymy or 2 for non-antonymy). A sample file could look like this:

	pos_tag	rel_class
maximum minimum	noun	1

Then features can be extracted for the file xx.tsv and the pairs can be classified. 
A sample python run could look like this:

python main.py --file xx.tsv --extract_features 3 --classify_features 3

--extract_features needs an integer list with integers from 1 to 9. It specifies which feature categories should be extracted. Feature categories are represented be the python enum FeatureCategory:

class FeatureCategory(Enum):
    COOC_PAIR = 1
    COOC_CONTEXT = 2
    LIN = 3
    JB_SIM = 4
    MORPH = 5 
    WORD_EMBED = 6
    PATTERNS = 7
    PARA_COOC_PAIR = 8
    WEB1T_PATTERNS = 9

COOC_PAIR is the association of the pairs in the corpus cc1 regarding a window of one sentence.
COOC_CONEXT are association scores of the word pairs with words in their sentence context in corpus cc1.
LIN are association scores with the patterns "either X or Y" and "from X to Y" in a corpus with 105 million sentences.
JB_SIM contains information of the distributional similarity of the words calculated with the JoBimText framework.
MORPH contains information about e.g. morphological antonym patterns like "un-" and lexical similarity of the words.
WORD_EMBED is the similarity of the SKIP-N-gram word embeddings.
PATTERNS contains pattern association scores.
PARA_COOC_PAIR contains association scores of the pairs in the corpus cc2.
WEB1T_PATTERNS contains associatino scores with pattern in the Google N-gram corpus. 

To make COOC_PAIR and COOC_CONTEXT work the corpus cc1 has to be specified in config/config.json e.g.:

"corpus_dir":"../Corpora/JoBimText"

And the number of sentences in the corpus cc1 has to be specified e.g.:

"num_sen_corpus":"105000000" 

To make PARA_COOC_PAIR work the corpus cc2 has to be specified e.g.:

"corpus_dir_aquaint":"../Corpora/Aquaint"

For WEB1T_PATTERNS the path to the Google N-gram corpus has to be specified e.g.:
 
"corpus_dir_web1t":"../../../../../Volume/web1t/"

For MORPH the path to the directory which contains the hyphen dir for pyhypen has to be specified e.g.:

"hyphen_dir": "res"


cc1 has to be in the format of this example sentence and zipped to .gz. First the sentence, then a tab, then the sentence with pos tags, then a tab, then the sentence parsed by a dependency parser (the depedency parse can be left out and substituted by a dummy string):

Evidently, quite a few.	Evidently/RB ,/, quite/RB a/DT few/JJ ./. 	evidently||RB dep||quite||RB;;;;;quite||RB -dep||evidently||RB;;;;;few||JJ det||a||DT;;;;;a||DT -det||few||JJ;;;;;quite||RB pobj||few||JJ;;;;;few||JJ -pobj||quite||RB;;;;;	dep(Evidently-1;quite-3);det(few-5;a-4);pobj(quite-3;few-5);

cc2 has to be one paragraph per line

PATTERNS would have to be extracted with the scala project. Therefor a resource id for xx.tsv has to be specified in the json file and the scores have to be computed by calling the function extractPatternFeaturesResId(resId) in Main.scala with this resId. (Since the google corpus is much larger Patterns is not really needed, it will make the system only slightly better).

--classify_features needs an integer list with integers from 1 to 9. It specifies which feature categories should be used for classification.

The call "python main.py --file xx.tsv --extract_features 3 --classify_features 3" thus extracts the Lin patterns association scores (these were calculated on a 105 million sentences corpus) and classifies the file according the theses scores. This would be a easy and fast way to get precise information about antonymy, since Lin patterns work quite well. But recall is quite low. 

"python main.py --file xx.tsv --extract_features 9 --classify_features 9" most probably takes 3 to 4 hours and needs the Google N-Gram corpus. 

