#check number of columns in original data: should be 13
original_path="/Users/admin/tmp-deskin/hyunjung/data/calor-doc"

find $original_path -type f -name "*.conllu" | while read conllu; do
    num_col=$(awk '{print NF}' $conllu | sort -nu | tail -n 1)
    if [[ !  $num_col == 13 ]]; then
        echo $conllu  $num_col
    fi
done

#START!!!!!!!!!
path=/Users/admin/tmp-deskin/hyunjung/data/CorefUD_French-CALOR-doc

#RUN PYTHON FILE: should check the input/output file path
echo "Starting to run the python code.."
cd $path
mkdir dev_tmp test_tmp train_tmp
python /Users/admin/tmp-deskin/hyunjung/script/corefUD/convert2corefUD/corefUD.py --dataset "dev_tmp" "test_tmp" "train_tmp"
# cp -r /Users/admin/tmp-deskin/hyunjung/data/CorefUD_French-CALOR-doc /Users/admin/tmp-deskin/hyunjung/data/CorefUD_French-CALOR-doc_done_python

##check number of columns in modified data: should be 14
find $path -type f -name "*.conllu" | while read conllu; do
    num_col=$(awk '{print NF}' $conllu | sort -nu | tail -n 1)
    if [[ !  $num_col == 14 ]]; then
        echo $conllu  $num_col
    fi
done


#MODIFY NUMBER OF COLUMNS (14 -> 10)
find $path -type f -name "*.conllu" | while read conllu; do
    while IFS= read -r line; do  
        echo "$(awk 'BEGIN {OFS="\t"} {print $1,$2,$3,$4,$5,$6,$7,$8,$9,$14}' $line)" > $line
    done 
done


#CHECK THE NUMBER OF COLUMNS
find $path -type f -name "*.conllu" | while read conllu; do
    num_col=$(awk '{print NF}' $conllu | sort -nu | tail -n 1)
    if [[ !  $num_col == 10 ]]; then
        echo $conllu  $num_col
    fi
done

##always getting a problem with this file: not anymore :) 
# prob="/Users/admin/tmp-deskin/hyunjung/data/calor-doc/dev/prehistoire@007ef79e-40cc-431e-a12a-b7c50c9ebae8.conllu"
save="/Users/admin/tmp-deskin/hyunjung/data/CorefUD_French-CALOR-doc/dev_tmp/prehistoire@007ef79e-40cc-431e-a12a-b7c50c9ebae8.conllu"
# awk '{print NF}' $prob | sort -nu | tail -n 1
# awk '{print NF}' $save | sort -nu | tail -n 1
echo "$(awk 'BEGIN {OFS="\t"} {print $1,$2,$3,$4,$5,$6,$7,$8,$9,$14}' $save)" > $save


#ADD TEXT ID and SENT ID
echo "Adding meta data.."

cd $path
for set_type_tmp in *_tmp; do
    set_type=$(echo $set_type_tmp | sed 's/_tmp//g') ###

    mkdir $path/$set_type

    cd $path/$set_type_tmp
    for file in *; do 
        filename=$(basename "$file" .conllu)

        echo "# newdoc id = $file" > $path/$set_type/$filename.tmp.conllu
        echo "# global.Entity = eid-etype-head-other" >> $path/$set_type/$filename.tmp.conllu
        echo "# sent_id = $file-s0" >> $path/$set_type/$filename.tmp.conllu

        i=0
        cat $file | while read line; do
            if [ "$line" == "" ]; then
                i=$((i+1))
                echo >> $path/$set_type/$filename.tmp.conllu
                echo "# sent_id = $file-s$i" >> $path/$set_type/$filename.tmp.conllu
            else
                echo "$line" >> $path/$set_type/$filename.tmp.conllu
            fi
        done
        #if last occurence of "# sent_id =", change it by empty string
        tac $path/$set_type/$filename.tmp.conllu| sed '0,/# sent_id =/{s/# sent_id =.*//}' | tac > $path/$set_type/$filename.conllu
    done
    echo "Done with $set_type_tmp set."
    
    cd $path
    rm $path/$set_type/*.tmp.conllu
    rm -rf $path/$set_type_tmp
done 
echo 
echo "Done adding meta data to the entire dataset."


#CONCATENATE THE FILES BY SET TYPE
cd $path
for set_type in *; do
    if [ -d "$set_type" ]; then
        cd $path/$set_type
        for file in *; do (cat "${file}"; echo) >> $path/fr_calor-corefud-$set_type.conllu.tmp; done
    fi

    #remove two or more empty lines
    cat -s $path/fr_calor-corefud-$set_type.conllu.tmp > $path/fr_calor-corefud-$set_type.conllu
    rm $path/fr_calor-corefud-$set_type.conllu.tmp

    cd $path
done