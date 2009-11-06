#Script for deploying
[deploy]
PRINT Running the deploy script...
python $source_dir/build/googlecode_upload.py -s "${product_name} ${product_version} ${os_abbrev} Installer" -p ramses-build -u gaberudy@gmail.com -w ${google_password} -l "Featured,Type-Installer,${os_type}" ${base_dir}/${local_package_dir}/${final_package_name}