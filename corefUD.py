#will have to add textID 

import os,sys
import argparse

import coref_info as pre

#remove line having only the line number at the end
def remove_line_num(tokens):
    new_tokens = []
    
    for token in tokens:
        if not all([isinstance(item, int) for item in token]):
            new_tokens.append(token)
        else:
            new_tokens.append([])
    return new_tokens


def extract_coref(tokens, coref_info_list):
    new_tokens, entityID_list = [], []

    for coref_dic in coref_info_list:
        current_entityID = coref_dic["entityID"]
        entityID_list.append(current_entityID)
        # print(current_entityID)
        
    for current_line in tokens: 
            if len(current_line) > 1:
                current_line[-1] = current_line[-1].replace('\n','')
                current_coref_str = current_line[-1]
                current_coref_list = current_coref_str.split('|')
                # print(current_coref_list)
                
                new_coref_list = []
                for coref in current_coref_list:
                    if coref.endswith(tuple(entityID_list)):
                        # if ("MENTION:" in coref) or ("COREF" in coref) and ("COREF-PRONOM" not in coref):
                        if ("MENTION:" in coref) or ("COREF" in coref):
                            new_coref_list.append(coref)

                if len(new_coref_list) != 0:
                    current_line.append('|'.join(new_coref_list))
                else:
                    current_line.append('_') 
            else:
                current_line = ['\n']
                
            new_tokens.append(current_line)
    return new_tokens                         
                    
                    
                
def extract_coref_seg(tokens, coref_info_dic):
    new_tokens = []
    current_entityID = list(coref_info_dic.items())[0][1]
 
    for current_line in tokens: 
        if len(current_line) > 1:
            current_line[-1] = current_line[-1].replace('\n','')
            current_coref_str = current_line[-1]
            current_coref_list = current_coref_str.split('|')

            new_coref_list = []
            for coref in current_coref_list:
                #이게 문제될 수도 있겠는걸?
                if coref.endswith(current_entityID):
                    # if ("MENTION:" in coref) or ("COREF" in coref) and ("COREF-PRONOM" not in coref):
                    if ("MENTION:" in coref) or ("COREF" in coref):
                        new_coref_list.append(coref)

            if len(new_coref_list) != 0:
                current_line.append('|'.join(new_coref_list))
            else:
                current_line.append('_') 
        else:
            current_line = ['\n']
            
        new_tokens.append(current_line)
    return new_tokens 


def b_alone(tokens):
    new_tokens = []
    
    for index, current_line in enumerate(tokens): 
        if len(current_line) != 1:
            current_coref_str = current_line[-1]
            current_coref_list = current_coref_str.split('|')
            
            new_coref_list = []
            for coref in current_coref_list:
                if index < len(tokens) - 1:
                    #if B:COREF-PRONOM:G:774 and next row also B:COREF-PRONOM:G:774
                    if coref.startswith('B:') and (coref in tokens[index+1][-1]):
                        new_coref = 'CS:'+ coref  #single
                        new_coref_list.append(new_coref)
                    elif coref.startswith('B:') and (coref[1:] not in tokens[index+1][-1]):
                        new_coref = 'CS:'+ coref  #single
                        new_coref_list.append(new_coref)
                    #if multiple 
                    else:
                        new_coref_list.append(coref)
                else:
                    if coref.startswith('B:'):
                        new_coref = 'CS:'+ coref 
                        new_coref_list.append(new_coref)
                    else:
                        new_coref_list.append(coref)
                        
            if len(new_coref_list) != 0:
                current_line.append('|'.join(new_coref_list))
            else:
                current_line.append('_')
            
        new_tokens.append(current_line)
    return new_tokens


def multiple_i(tokens):
    new_tokens = []
    
    for index, current_line in enumerate(tokens): 
        if len(current_line) != 1:
            #current_line[-1] = current_line[-1].replace('\n','')
            current_coref_str = current_line[-1]
            current_coref_list = current_coref_str.split('|')
            
            new_coref_list = []
            for coref in current_coref_list:
                if (index < len(tokens) - 1) and (len(tokens[index+1]) !=1):
                    if coref.startswith('B:') and (coref[1:] in tokens[index+1][-2]):
                        new_coref = 'CM:'+ coref #multiple
                        new_coref_list.append(new_coref)
                        
                    #if coref.startswith('I:') and (coref[1:] not in tokens[index+1][-2]):
                    if coref.startswith('I:') and (coref not in tokens[index+1][-2]):
                        new_coref = 'CM:'+ coref 
                        new_coref_list.append(new_coref)
                        
                    if coref.startswith('CS:B:'):
                        new_coref_list.append(coref)
                else:
                    if coref.startswith('I:'):
                        new_coref = 'CM:'+ coref 
                        new_coref_list.append(new_coref)
                        
            if len(new_coref_list) != 0:
                current_line[-1]='|'.join(new_coref_list)

        new_tokens.append(current_line)
    return new_tokens


def Entity_format(tokens):
    '''
    format: #Entity=(e32152--2
    '''
    new_tokens = []
    
    for current_line in tokens:
        if len(current_line) != 1:
            coref_string = current_line[-1]
            coref_list = coref_string.split('|')
            
            new_coref_list = []
            new_coref_list_single, new_coref_list_multiple_b, new_coref_list_multiple_i = [], [], []
            # single_entityID_list, multi_entityID_list_b, multi_entityID_list_i = [], [], []
            
            if coref_list != ['_']:
                for coref in coref_list:
                    entityID = coref.split('G:')[1]
                    if coref.startswith('CS:B:'):
                        new_coref_list_single.append(f'(e{entityID}--[head_token_id])')
                        # single_entityID_list.append(f'e{entityID}')
                    elif coref.startswith('CM:B:'):
                        new_coref_list_multiple_b.append(f'(e{entityID}--[head_token_id]')
                        # multi_entityID_list_b.append(f'e{entityID}')
                    elif coref.startswith('CM:I:'):
                        new_coref_list_multiple_i.append(f'e{entityID})')
                        # multi_entityID_list_i.append(f'e{entityID}')
            
            # remove_entityID_list = list(set(single_entityID_list) & set(multi_entityID_list))

            #remove item from new_coref_list_single if it is substring of an item of other remove_entityID_list
            #for such as: I:COREF-TARGET-DIRECT:G:13127|B:COREF-TARGET-INDIRECT:G:13127 in /Users/admin/tmp-deskin/hyunjung/data/calor-doc/ex/histwikiㄷf28cab92-a319-4349-ba07-e59c0c6709bf.conllu
            # for coref in new_coref_list_single:
            #     if any(remove_entityID in coref for remove_entityID in remove_entityID_list):
            #         new_coref_list_single.remove(coref)
        
            new_coref_list =  new_coref_list_single + new_coref_list_multiple_i + new_coref_list_multiple_b
            
            # if new_coref_list_single != []:
            #     new_coref_list = multi_entityID_list_i + new_coref_list_single + new_coref_list_multiple
            # else:
            #     new_coref_list = new_coref_list_multiple
            
            if len(new_coref_list) != 0:
                current_line[-1] = "Entity=" + ''.join(new_coref_list) + '\n'
            else:
                current_line[-1]='_\n'
        
        new_tokens.append(current_line)
    return new_tokens


def head_index(head_token_index_list):
    head_index_dic = {}
    
    for head_token_info in head_token_index_list:
        head_index_dic[head_token_info.split("_")[0]] = head_token_info.split("_")[1]      
    return head_index_dic


def modify_head_info(tokens, coref_info_list):
    
    for coref_info_dic in coref_info_list: 
        entityID = coref_info_dic['entityID']
        entityID_num = entityID.split("G:")[1]
        coref_chain_list = coref_info_dic['coref_chain']
        head_token_index_list = [element['head_token_index'] for element in coref_chain_list]
        
        head_index_dic = head_index(head_token_index_list)
        
        for token in tokens:
            if len(token) > 1:
                if (token[0] in head_index_dic.keys()) and (entityID_num in token[-1]):
                    #token[-1] = token[-1].replace('[head_token_id]', head_index_dic[token[0]])
                    # print(f"before: {token[-1]}")
                    replace_from = f"e{entityID_num}--[head_token_id]"
                    replace_to = f"e{entityID_num}--{head_index_dic[token[0]]}"
                    token[-1] = token[-1].replace(replace_from, replace_to)
                    # print(f"after: {token[-1]}")
    return tokens



def remove_duplicates(tokens):
    for token in tokens:
        if len(token) > 1:
            entities_list = token[-1].replace("\n","").split("|")
            entities_list = list(dict.fromkeys(entities_list))
            token[-1] = "|".join(entities_list) + "\n"
    return tokens



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--foo', action='append')
    parser.add_argument(
    "--dataset",  # name on the CLI - drop the `--` for positional/required parameters
    nargs="*",  # 0 or more values expected => creates a list
    type=str,
    default=["dev_tmp", "test_tmp", "train_tmp"],  # default if nothing is provided
    )
    
    args = parser.parse_args()
    dataset_list = args.dataset
    
    # dataset_list = ["dev_tmp", "test_tmp", "train_tmp"]
    # dataset_list = ["ex"]

    for dataset_tmp in dataset_list:
        dataset = dataset_tmp.replace("_tmp","") 
        print(f'Starting to convert {dataset} set.')
        
        open_path = f'/Users/admin/tmp-deskin/hyunjung/data/calor-doc/{dataset}/'
        os.chdir(open_path)
        
        for file in os.listdir():
            if file.endswith(".conllu"):
            # if file.endswith(".conllu") and file.startswith("antiquite@32fd"):
                #print(file)
                
                coref_info_list = pre.get_coref_info(open_path, file)
                
                tokens = pre.data_to_list(file)
                tokens = pre.add_sentID(tokens)
                tokens = pre.for_dep(tokens) 
                tokens = remove_line_num(tokens)
                tokens = extract_coref(tokens, coref_info_list)
                tokens = b_alone(tokens)
                tokens = multiple_i(tokens)
                tokens = Entity_format(tokens)
                tokens = modify_head_info(tokens, coref_info_list)
                tokens = remove_duplicates(tokens)

                save_path = f'/Users/admin/tmp-deskin/hyunjung/data/CorefUD_French-CALOR-doc/{dataset_tmp}/'
                # save_path = f'/Users/admin/Desktop/'

                with open(save_path + file, 'w') as f:
                    for token in tokens:
                        if len(token) != 1:
                            tokenID = token[0].split('ㄷ')[0].split('ㄱt')[1]
                            original_token = token[0].split('ㄷ')[1].split('ㄱ')[0]
                            add_token = [tokenID] + [original_token] + token[1:-2] + [token[-1]]
                        else:
                            add_token = token
                        f.write("\t".join(map(str, add_token)))
                
        print(dataset, '-----> DONE !!')
        
    print("\n-----------------------------")
    print("DONE WITH ALL DATASET.")   
