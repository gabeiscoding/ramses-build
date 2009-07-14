#Ramses build script

[clean_source]
PRINT Cleaning out source directory...
rm -rf $source_dir

[checkout_source]
PRINT Checking out source code
mkdir -p $product_name
svn co $svn_url $source_dir

[update_source]
PRINT Updating source code
svn update $source_dir

[clean_stagearea]
PRINT Cleaning up old Stage Area (all data will be lost)...
rm -rf $stagearea_dir
mkdir -p $stagearea_dir

[pyinstaller]
cd $source_dir; SVNREV=`svn info | grep "Revision" | grep -o "[0-9]\+"`; sed -e "s/_VMAJ/${version_major}/;s/_VMIN/${version_minor}/;s/_VBUG/${version_bug}/;s/_VERSION/${product_version}/;s/_DATE/${date_yymmdd}/;s/_PLATFORM/${os_abbrev}/;s/_YEAR/${date_yyyy}/;s/_REV/${SVNREV}/;" build/version.txt > ramses/version.txt
PRINT Running PyInstaller MakeSpec
PRINT ...
cd $source_dir/ramses; python $py_mkspec -o ${base_dir}/${stagearea_dir} --icon=../build/icon.ico --version=version.txt -n $product_name build.py
PRINT Running PyInstaller Build
PRINT ...
cd $source_dir/ramses; python $py_build ${base_dir}/$stagearea_dir/${product_name}.spec

[win_setup_package]
PRINT Making the installer in ${local_package_dir}
echo "#define MyAppName \"${product_name}\"" > ${source_dir}/install_script.iss
echo "#define MyAppVer \"${product_version}\"" >> ${source_dir}/install_script.iss
echo "#define MyAppVerName \"${product_name} ${product_version}\"" >> ${source_dir}/install_script.iss
echo "#define MyAppPublisher \"By Gabe Rudy\"" >> ${source_dir}/install_script.iss
echo "#define MyAppURL \"${product_website}\"" >> ${source_dir}/install_script.iss
echo "#define MyAppExeName \"${binary_name}.exe\"" >> ${source_dir}/install_script.iss
echo "#define MyPlatform \"${os_abbrev}\"" >> ${source_dir}/install_script.iss
echo "#define MyOutputDir \"${base_dir}/${local_package_dir}\"" >> ${source_dir}/install_script.iss
echo "#define MyStageDir \"${base_dir}/${stagearea_dir}/dist/${product_name}\"" >> ${source_dir}/install_script.iss
echo "#define MyScriptWriterPath \"${base_dir}/${source_dir}/build/write-launch-script.js\"" >> ${source_dir}/install_script.iss
echo "#define MySetupIconPath \"${base_dir}/${source_dir}/build/install.ico\"" >> ${source_dir}/install_script.iss

tail -n +11 ${source_dir}/build/setup.iss >> ${source_dir}/install_script.iss
"$istool_exe" -compile ${source_dir}/install_script.iss
