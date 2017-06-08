# coding=utf_8
import io
import xml.etree.ElementTree as et

############# HELPER FUNCTIONS #############

def digits_to_str(number):
    """Convert digit representation of a number into word representation."""
    segment_number_str = ""

    for digit in segment_number:
        if digit == '1':
            segment_number_str += 'One'
        elif digit == '2':
            segment_number_str += 'Two'
        elif digit == '3':
            segment_number_str += 'Three'
        elif digit == '4':
            segment_number_str += 'Four'
        elif digit == '5':
            segment_number_str += 'Five'
        elif digit == '6':
            segment_number_str += 'Six'
        elif digit == '7':
            segment_number_str += 'Seven'
        elif digit == '8':
            segment_number_str += 'Eight'
        elif digit == '9':
            segment_number_str += 'Nine'
        else:
            segment_number_str += 'Ten'

    return segment_number_str

############################################

# Parse XML (ELAN) file
tree = et.parse('Haneshwar.ready.for.elan.eaf')
# Get XML document root
root = tree.getroot()

output_file = io.open("lingex.sty", "w", encoding="utf-8")

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
            morph_elements = root.findall("./TIER[@TIER_ID='A_morph-txt-ajz-fonipa']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_REF='%s']" % word_id)

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
                        "Missing annotations replaced with '#MISSING#'.\n")
                    word_as_morphs.append("???")
                
                # Get glossary element pertaining to this morph
                gloss_elements = root.findall("./TIER[@TIER_ID='A_morph-gls-en']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_REF='%s']" % morph_id)
                for gle in gloss_elements:
                    word_gloss.append(gle[0].text)

            sent_as_morphs.append("".join(word_as_morphs))
            try:
                sent_glossary.append("".join([word_gloss[0]] + ["-%s" % gloss if gloss[0] != "=" else gloss for gloss in word_gloss[1:]]))
            except:
                pass

    # Find the English translation of the sentence
    for e in root.findall("./TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_REF='%s']" % ('A_phrase-gls-en', seg_id)):
        sentence_english = e[0].text

    latex_cmd = "\\begin{exe}\n\\ex\n\\gll %s\\\\\n%s\\\\\n\\trans '%s'\n\\end{exe}\n" \
        % (" ".join(sent_as_morphs), u" ".join(sent_glossary), sentence_english)
    
    # Get the number identifying this utterance
    segment_number = seg[0][0].text
    # Convert digits into words for Latex command
    segment_number_str = digits_to_str(segment_number)
    
    # Write the macro for the utterance into the lingex.sty file
    output_file.write("\\newcommand{\\utterance%s}{\n%s}\n" % (segment_number_str, latex_cmd))

output_file.close()


