const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
module.exports=file=>{
  const {version}=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../js/asset-version.json'),'utf8'));
  return import(pathToFileURL(path.resolve(__dirname,'../js',file.split('?')[0])).href+'?v='+version);
};
