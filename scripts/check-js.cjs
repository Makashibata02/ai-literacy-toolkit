// Run the shipped browser search implementation without remote dependencies.
const fs=require('node:fs'),vm=require('node:vm');
const context={window:{},document:{getElementById:()=>null},console};vm.createContext(context);
vm.runInContext(fs.readFileSync('site/search-index.js','utf8'),context);
vm.runInContext(fs.readFileSync('site/assets/app.js','utf8'),context);
const cases=JSON.parse(fs.readFileSync('tests/retrieval-cases.json','utf8'));
const results=cases.map(c=>({query:c.query,top3:context.window.ToolKitSearch.search(c.query,3).map(r=>r.id)}));
process.stdout.write(JSON.stringify(results));
