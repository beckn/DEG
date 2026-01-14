find . -name "*.md" -not -path "./ref_docs/*" | xargs python3 scripts/check_links.py 2>&1 | tee 
   link_check_full_output.txt