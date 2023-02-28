import os
import re
import string
from collections import Counter 
from itertools import tee, count

from datetime import date
today = date.today().strftime("%y%m%d")

# function to transform the conll file to a matrix (list of lists)
def data_to_list(file_path) :
    tokens = []

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file : 
            ##mind that empty lines also have ids. If you don't wan't to count them, skip empty lines 
            line = line.split('\t')
            line[0] = 't'+line[0]
            tokens += [line]    
    return tokens


def add_sentID(tokens):
    new_tokens = []
    i = 0 
    for line in tokens:
        if len(line) == 1:
            i += 1
        else:
            line.insert(0, 's'+str(i))
        new_tokens.append(line)
    return new_tokens 
  
  
def for_dep(tokens):
    new_tokens = []
    for line in tokens:
        new_line = line[2:]
        if len(line) != 1:
            new_line[0] = line[0] + 'ㄱ' + line[1]+'ㄷ'+line[2] + 'ㄱ'+ line[4] + 'ㄱ'+ line[7] #여기 고쳤어
        new_tokens.append(new_line)
    return new_tokens 
  

# function to transform the conll file to a matrix (list of lists)
def numbering(tokens) :
    i=0
    for line in tokens : 
        ##mind that empty lines also have ids. If you don't wan't to count them, skip empty lines 
        line.insert(0,i)
        i += 1
    tokens.append([i]) #had to add an empty because of some issues with the last line of some files (those having only one empty line at the end)   
    return tokens


# function to associate each sentence with their first/last word index
def sentence_id(sentences):
    list_of_sentences = []

    sentence = ''
    first_word_index, last_word_index = 0, 0
    for line in sentences:
        if len(line) == 1:
            last_word_index = line[0]-1
            tuple_ = (sentence, first_word_index, last_word_index)
            sentence = ''
            first_word_index = line[0]+1
            list_of_sentences.append(tuple_)
        else:
            sentence = line[1] if (len(sentence)<1) else sentence + line[1] if (line[1] in string.punctuation) or (sentence[-1] == "'") else sentence + " " + line[1]

    return list_of_sentences


#function to build a ditionary that contains the ids_coref and their ids of order
def coref_and_id(tokens) :
    dict_ = {}

    for line in tokens: #details of each token = each line of the conllu file
        coref = line[-1] #the last column ('COREF')
        #if does contain coref: 1) not empty line(=doesn't contains numbers) 2) not '_\n'
        if (str(coref).isdecimal()== False) & (str(coref)!='_\n'): 
            #not those starting with 'B:', but rather those containing 'B:'
            if 'B:' in coref:
                if ('|') in str(coref):    
                    list_ = coref.split('|')
                else:
                    list_ = [coref]

                #remove elements with 'I:' 
                list_ = [coref for coref in list_ if not coref.startswith('I:')]
                
                for coref in list_:
                    coref = coref.split(':')
                    key = coref[-2]+':'+ re.sub('\n', '', (coref[-1]))
                    if key in dict_.keys():
                        dict_[key] += [str(line[0])+"ㄷ"+coref[1]] #여기 tokenID 였어...
                    else :
                        dict_[key] = [str(line[0])+"ㄷ"+coref[1]]
                dict_[key] = sorted(list(set(dict_[key])))  # le set pour enlever les ids qui se répètent (Le cas des coréferences autonomes)
    return dict_
 

#filter non-relevant entityID
#filter coref type
def filter_dic(dict_, filename):
    new_dict_ = {}
    
    for entityID, coref_list in dict_.items():
        new_coref_list = []
        for coref in coref_list:
            #"MENTION_ANAPHOR" "MENTION-UNKNOWN" "MENTION-SITUATIONNELLE"
            #if ("COREF-PRONOM" not in coref) and ("MENTION_" not in coref) and ("MENTION-" not in coref):
            if ("MENTION_" not in coref) and ("MENTION-" not in coref):
                new_coref_list.append(coref)
        if new_coref_list != []:
            new_dict_[entityID] = new_coref_list
    return new_dict_
   

#function to extract a coref sequence, '<>' added around corefs/mentions
def extract_context(entityID, coref_start_position_and_coref_type, tokens, list_of_sentences):
    coref_start_position = int(coref_start_position_and_coref_type.split("ㄷ")[0]) #eg. '102ㄷMENTION' 
    coref_type = coref_start_position_and_coref_type.split("ㄷ")[1]
    
    id_start, id_finish = coref_start_position, coref_start_position
    coref_sen = [sentence for sentence in list_of_sentences  if (sentence[1] <= id_start <= sentence[2])]
    
    if len(coref_sen) != 0: #if coref_sen is not empty
        id_sen_start = coref_sen[0][1]
        id_sen_finish  = coref_sen[0][2]
        context = ''
        whole_dep = '' 

        #while it contains the coreference entity id and the 'I:' string 
        next_coref_type = "I:"+ str(coref_type)+":"+str(entityID) + "($|\||\n)"
        while (re.search(next_coref_type, str(tokens[id_finish+1][-1])) is not None):
            id_finish += 1

        for i in range (id_sen_start, id_sen_finish+1):
            if i == id_start:
                context += '<'
                whole_dep += '<'
                
            if i == id_finish:
                context += tokens[i][1].split('ㄷ')[1].split('ㄱ')[0]
                context += '> '
                whole_dep += tokens[i][1]
                whole_dep += '> '
                
            else :
                context += tokens[i][1].split('ㄷ')[1].split('ㄱ')[0] + ' '
                whole_dep += tokens[i][1] + ' '
    else:
        context, whole_dep, id_start, id_finish, coref_type = None, None, None, None, None
    return (context, whole_dep, id_start, id_finish, coref_type)
    
 
def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3


def _next_level_dic(dep1_dic, text):
    dep2_dic = {}
    for first_level_item, second_level_list in dep1_dic.items():
        if isinstance(second_level_list, list):
            for second_level_item in second_level_list:
                second_level_tokenID = second_level_item.split('ㄷ')[0].split('ㄱ')[1].replace('t','')
                second_level_sub_items = [word for word in text.split() if word.endswith("ㄱ"+second_level_tokenID)]
                if len(second_level_sub_items) != 0:
                    dep2_dic[second_level_item] =[word for word in text.split() if word.endswith("ㄱ"+second_level_tokenID)]
    return dep2_dic
    

def _when_found_no_head(mention_info):
    head_info = ''
    # Select a word in preference of a pos order
    mention_item_list = mention_info.split()
    mention_pos_list = [item.split("ㄱ")[-2] for item in mention_item_list]
    
    # If all words have identical pos, then select the first one  
    if len(set(mention_pos_list)) == 1:
        head_info = mention_item_list[0]
    else:
        pos_order = ['ㄱPROPNㄱ','ㄱNOUNㄱ','ㄱADJㄱ','ㄱADVㄱ','ㄱVERBㄱ']
        
        for pos in pos_order: 
            #check if mention_item_list has a pos from pos_order
            #it may have multiple match, in that case, choose the first one
            matched_mention_item = [item for item in mention_item_list if pos in item]
            
            #whether it has one or multiple matches, choose the first one
            if len(matched_mention_item) != 0:
                head_info = matched_mention_item[0]
        
        if head_info == '':
            head_info = mention_item_list[0]
    return head_info

    
def _get_head(text):
    head_info = ""
    mention_info = text.split('<')[1].split('>')[0]
    
    if len(mention_info.split()) == 1:
        head_info = mention_info
    else:
        text = text.replace('<','')
        text = text.replace('>','')
        
        root_info = [word for word in text.split() if word.endswith("ㄱ0")][0]
        root_tokenID = root_info.split('ㄷ')[0].split('ㄱ')[1].replace('t','')
        
        if root_info in mention_info.split():
            head_info = root_info
        else:
            dep1_dic = {}
            first_level_list = [word for word in text.split() if word.endswith("ㄱ"+root_tokenID)]
            for first_level_item in first_level_list:
                first_level_tokenID = first_level_item.split('ㄷ')[0].split('ㄱ')[1].replace('t','')
                first_level_sub_items = [word for word in text.split() if word.endswith("ㄱ"+first_level_tokenID)]
                if len(first_level_sub_items) != 0:
                    dep1_dic[first_level_item] = first_level_sub_items
                else:
                    dep1_dic[first_level_item] = first_level_item    

            intersection_list = intersection(mention_info.split(), dep1_dic.keys())
            
            if len(intersection_list) != 0:
                head_info = intersection_list[0]
            else: 
                length_sen = len(text.split())
                for i in range(0,length_sen):
                    dep2_dic = _next_level_dic(dep1_dic, text)
                    
                    intersection_list = intersection(mention_info.split(), dep2_dic.keys())
                    
                    if len(intersection_list) != 0:
                        head_info = intersection_list[0]
                        break
                    else:
                        dep1_dic = dep2_dic.copy()
                        i += 1
            
                if head_info == "":
                    head_info = _when_found_no_head(mention_info)
    return head_info


# function to extract characteristics of the corefs
def extract_coref_chain(entityID, coref_start_position, tokens, list_of_sentences):
    dict_coref = {}

    #context
    context = str(extract_context(entityID, coref_start_position, tokens, list_of_sentences)[0])
    
    #expression
    expression = context.split('<')[1].split('>')[0]
    dict_coref['expression'] = expression
        
    #span
    # dict_coref['span_begin'] = extract_context(entityID, coref_start_position, tokens, list_of_sentences)[2]
    # dict_coref['span_end'] = extract_context(entityID, coref_start_position, tokens, list_of_sentences)[3]   
    dict_coref['span'] = (extract_context(entityID, coref_start_position, tokens, list_of_sentences)[2], extract_context(entityID, coref_start_position, tokens, list_of_sentences)[3])
    
    #head
    extract_dep_element = str(extract_context(entityID, coref_start_position, tokens, list_of_sentences)[1])
    
    head_info = _get_head(extract_dep_element)
    head_token = head_info.split("ㄷ")[1].split("ㄱ")[0]
    dict_coref['head_word'] = head_token

    dep_expression_list = extract_dep_element.split('<')[1].split('>')[0].split()
    first_dep = dep_expression_list[0]
    head_token_index = dep_expression_list.index(head_info) + 1#might have some problems if head_info==""
    #dict_coref['head_token_index'] = head_token_index
    dict_coref['head_token_index'] = f'{first_dep}_{head_token_index}'
    
    #coref type
    #original version of "MENTION"
    dict_coref['coref_type'] = extract_context(entityID, coref_start_position, tokens, list_of_sentences)[4]

    #second version of "MENTION": "MENTION-PRON"
#     coref_type = extract_context(entityID, coref_start_position, tokens, list_of_sentences)[-1]
#     if coref_type == 'MENTION':
#         extract_dep_element = extract_dep_element.split('<')[1].split('>')[0]
#         if (len(extract_dep_element.split()) == 1):
#             pos = extract_dep_element.split('#')[-2]
#             if pos == 'PRON':    
#                 coref_type = coref_type+'-PRON'
#     dict_coref['coref_type'] = coref_type
    return dict_coref

    
def get_coref_info(path, filename):
    # Change the directory
    os.chdir(path)
    
    tokens = data_to_list(filename)
    tokens = add_sentID(tokens)
    tokens = for_dep(tokens) 
    tokens = numbering(tokens) 
    
    list_of_sentences = sentence_id(tokens)
    
    dict_ = coref_and_id(tokens) 
    new_dict_ = filter_dic(dict_, filename)
    
    final_coref_chain_list = []
    coref_chain_dic = {}

    # print(new_dict_)
    
    for entityID in new_dict_.keys() :
        coref_chain_dic = {}
        coref_chain_list = []
        for position in new_dict_[entityID]: #iterate all positions of an entity
            if extract_context(entityID, position, tokens, list_of_sentences) != (None, None, None, None):
                coref_chain_list.append(extract_coref_chain(entityID, position, tokens, list_of_sentences))  

        coref_chain_dic['entityID'] = entityID
        coref_chain_dic['coref_chain'] = coref_chain_list
        final_coref_chain_list.append(coref_chain_dic)
    
    #I actually would have a dictionary about one entity
    return final_coref_chain_list

