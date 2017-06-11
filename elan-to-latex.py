# coding=utf_8
import io
import xml.etree.ElementTree as et
import sys
import getopt
import re

def read_config(filepath):
    """Read the script configuration file"""
    try:
        f = open(filepath, "r")
        
        input_files = []
        output_file = ""
        small_caps_list = []
        
        mode = ""

        for line in f:
            if line[0] == "#":
                continue
            elif line[:-1] == "/ELAN INPUT FILES":
                mode = "in"
            elif line[:-1] == "/OUTPUT FILE":
                mode = "out"
            elif line[:-1] == "/SMALL CAPS LIST":
                mode = "cap"
            elif line != "\n":
                if mode == "in":
                    input_files.append(line[:-1])
                elif mode == "out":
                    output_file = line[:-1] 
                elif mode == "cap":
                    small_caps_list.append(line[:-1])
  
    except FileNotFoundError:
        print("You supplied an invalid configuration file or the default file doesn't exists")
        sys.exit(2)

    return (input_files, output_file, small_caps_list)

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "i:", ["input="])
    except getopt.GetoptError:
        print("Something went wrong.")
        sys.exit(2)

    # Default configuration file
    filename_in = 'etl_conf'

    # Get config filename from command line arguments
    for opt, arg in opts:
        if opt in ('-i', '--input'):
            filename_in = arg

    # Read the configuration file into the tuple config_parameters
    config_parameters = read_config(filename_in)
    input_files = config_parameters[0]
    output_file = config_parameters[1]
    small_caps = config_parameters[2]
    
    output_file = io.open(output_file, "w", encoding="utf-8")
    
    # Filter for non-alphabetic characters
    filt = re.compile('[^a-zA-Z]')

    for filename_in in input_files:
        # Parse XML (ELAN) file
        try:
            tree = et.parse(filename_in)
        except FileNotFoundError:
            print("You supplied an invalid input file. Filename: %s" % filename_in)
            sys.exit(2)

        # Get XML document root element
        root = tree.getroot()

        # Get segment tier which contais all speech segments
        segment_tier = root.find("./TIER/[@TIER_ID='A_phrase-segnum-en']")

        for seg in segment_tier:
            # Reference id for the sentence (segment) currently being handled
            seg_id = seg[0].get("ANNOTATION_ID")

            # Find the the XML elements representing the target language words
            word_elements = root.findall("./TIER[@TIER_ID='A_word-txt-ajz-fonipa']/ANNOTATION/REF_ANNOTATION/[@ANNOTATION_REF='%s']" % (seg_id))

            # Initialize sentence as list
            sent_target_lang = []
            sent_as_morphs = []
            sent_glossary = []

            # Go through word elements
            for e in word_elements:
                # Reference id for the word
                word_id = e.get("ANNOTATION_ID")

                if e[0].text != None:
                    # Add word to sentence
                    sent_target_lang.append(e[0].text)

                    # Find the elements representing the individual morphemes pertaining to this word
                    morph_elements = root.findall("./TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_REF='%s']" % ("A_morph-txt-ajz-fonipa", word_id))

                    word_as_morphs = []
                    word_gloss = []

                    for me in morph_elements:
                        # Reference id for the morpehe
                        morph_id = me.get("ANNOTATION_ID")

                        # Extract morph if presents, otherwise substitute '???'
                        if me[0].text != None:
                            word_as_morphs.append(me[0].text)
                        else:
                            print("SEGMENT %s: It seems like some annotations are missing. " % seg[0][0].text +
                                "Missing annotations replaced with '#MISSING#'.")
                            word_as_morphs.append("???")

                        # Get glossary element pertaining to this morph
                        gloss_elements = root.findall("./TIER[@TIER_ID='A_morph-gls-en']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_REF='%s']" % morph_id)
                        # Build the list of gloss elements
                        for gle in gloss_elements:
                            only_alpha = filt.sub("", gle[0].text)
                            if only_alpha in small_caps:
                                word_gloss.append("{\sc %s}" % gle[0].text)
                            else:
                                word_gloss.append(gle[0].text)                                

                    sent_as_morphs.append("".join(word_as_morphs))
                    try:
                        sent_glossary.append("".join([word_gloss[0]] + ["-%s" % gloss if gloss[0] != "=" else gloss for gloss in word_gloss[1:]]))
                    except:
                        pass

            # Find the English translation of the sentence
            for e in root.findall("./TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_REF='%s']" % ('A_phrase-gls-en', seg_id)):
                sentence_english = e[0].text

            # Get the number identifying this utterance
            segment_label = seg[0][0].text
            # Convert digits into words for Latex command
            segment_label_ltx, segment_reference = seg_label_to_cmd_and_ref(segment_label)

            # Construct the latex command string
            latex_cmd = "\\begin{exe}\n\\ex\n{\it %s}\n\\gll %s\\\\\n%s\\\\\n\\trans '%s' [%s]\n\\end{exe}\n" \
                % (" ".join(sent_target_lang), " ".join(sent_as_morphs), u" ".join(sent_glossary), sentence_english, segment_reference)

            # Write the macro for the utterance into the lingex.sty file
            output_file.write("\\newcommand{\\%s}{\n%s}\n\n" % (segment_label_ltx, latex_cmd))

    output_file.close()

############# HELPER FUNCTION #############

def seg_label_to_cmd_and_ref(segment_label):
    """Convert digit representation of a number into word representation."""
    segment_label_cmd = ""
    segment_reference = ""

    for c in segment_label:
        if c != "_":
            segment_reference += c
        else:
            segment_reference += " "

        if c == '1':
            segment_label_cmd += 'One'
        elif c == '2':
            segment_label_cmd += 'Two'
        elif c == '3':
            segment_label_cmd += 'Three'
        elif c == '4':
            segment_label_cmd += 'Four'
        elif c == '5':
            segment_label_cmd += 'Five'
        elif c == '6':
            segment_label_cmd += 'Six'
        elif c == '7':
            segment_label_cmd += 'Seven'
        elif c == '8':
            segment_label_cmd += 'Eight'
        elif c == '9':
            segment_label_cmd += 'Nine'
        elif c == '0':
            segment_label_cmd += 'Zero'
        elif c == '_':
            pass
        else:
            segment_label_cmd += c

    return segment_label_cmd, segment_reference

###########################################

if __name__ == "__main__":
    main(sys.argv[1:])
