// Contract and request-count checks with in-memory responses only; no API writes.
const assert=require('node:assert/strict');
const mod=require('./frontend-module.cjs');
(async()=>{
  global.window={location:{hostname:'example.test',port:'',href:'https://example.test/',search:''}};
  global.localStorage={getItem:()=>null};
  const {API_CONFIG}=await mod('api/config.js');
  assert.equal(API_CONFIG.CATALOG_V2,true);assert.equal(API_CONFIG.SPLICE_DETAIL,true);assert.equal(API_CONFIG.BASE_URL,'/api');
  const {apiClient}=await mod('api/apiClient.js');
  const {configuratorApi}=await mod('api/configuratorApi.js');
  let gets=0;
  apiClient.get=async()=>{gets++;return {settings:{},extras:[{id:1,billing_type:'per_meter'},{id:2,billing_type:'fixed'}],splice_materials:[],splice_types:[{id:1,category:'loop'},{id:2,category:'splice'}],splice_price_rules:[{splice_type_id:1},{splice_type_id:2}],rope_products:[]};};
  const [rope,loops,splices]=await Promise.all(['rope_with_splice','loop_only','splice_only'].map(type=>configuratorApi.getData(type,'rus')));
  assert.equal(gets,1);assert.equal(rope.extras.length,2);assert.equal(loops.extras.length,1);assert.equal(splices.splice_types[0].id,2);assert.equal(loops.splice_price_rules[0].splice_type_id,1);
  loops.extras[0].id=99;assert.equal(rope.extras[1].id,2);
  await configuratorApi.getData('rope_with_splice','rus',{refresh:true});assert.equal(gets,2);
  apiClient.get=async()=>{throw Error('offline');};
  await assert.rejects(configuratorApi.getData('rope_with_splice','rus',{refresh:true}));
  apiClient.get=async()=>({settings:{},extras:[],splice_materials:[],splice_types:[],splice_price_rules:[],rope_products:[]});
  await configuratorApi.getData('rope_with_splice','rus');

  const {contactsApi}=await mod('api/contactsApi.js');
  apiClient.get=async()=>assert.fail('Public contacts must not call protected routes');
  assert.equal(await contactsApi.get(),null);
  apiClient.get=async endpoint=>{assert.equal(endpoint,'/settings');return {company_name:'Company',contact_email:'company@example.test',contact_phone:'+491234567'};};
  assert.equal((await contactsApi.getAdmin()).name,'Company');
  apiClient.patch=async(endpoint,data)=>{assert.equal(endpoint,'/settings');assert.deepEqual(Object.keys(data).sort(),['company_name','contact_email','contact_phone']);return data;};
  await contactsApi.save({name:'Company',email:'company@example.test',phone:null,message:'not part of settings'});

  const {adminConfigApi}=await mod('api/adminConfigApi.js');
  const {AdminConfigController}=await mod('controllers/AdminConfigController.js');
  for(const [section,expected] of [['categories',['categories']],['splice_types',['splice_types']],['splice_prices',['splice_prices','splice_types','splice_materials']],['links',['rope_products','splice_types']]]){
    const requested=[];adminConfigApi.list=async name=>{requested.push(name);return [];};
    const controller=Object.create(AdminConfigController.prototype);
    controller.section=section;controller.view={allowDiscard:()=>true,busy(){},message(){},clear(){},list(){},render(){}};
    await controller.load();assert.deepEqual(requested,expected);assert.equal(controller.busy,false);assert.equal(controller.ready,true);
  }

  const {adminColorsApi}=await mod('api/adminColorsApi.js');
  gets=0;apiClient.get=async()=>{gets++;return [];};
  await adminColorsApi.list({refresh:true});await adminColorsApi.list();assert.equal(gets,1);
  apiClient.patch=async()=>{throw Error('partial update');};await assert.rejects(adminColorsApi.update(1,{}));
  await adminColorsApi.list();assert.equal(gets,2);

  const {reviewsApi}=await mod('api/reviewsApi.js');
  const items=Array.from({length:60},(_,id)=>({id:id+1,author_name:'Test',text:'Review',index:id}));
  gets=0;
  apiClient.get=async(endpoint,options)=>{gets++;assert.equal(endpoint,'/reviews');const p=options.params;return {items:p.status==='new'?items.slice(0,20):p.status==='rejected'?items.slice(20,40):p.is_published?items.slice(40,50):items};};
  const reviews=await reviewsApi.list('rus',true);
  assert.equal(gets,4);assert.equal(reviews.items[0].status,'new');assert.equal(reviews.items[22].status,'rejected');assert.equal(reviews.items[45].is_published,true);assert.equal(reviews.items[55].is_published,false);
  const review={id:1,author_name:'Test',rating:5,index:0,status:'confirmed',is_published:true,translations:[{id:7,locale:'rus',text:'Same'}]};
  apiClient.get=async()=>review;
  apiClient.patch=apiClient.post=apiClient.delete=async()=>assert.fail('Unchanged review must not write');
  await reviewsApi.save(1,review);

  const {siteContentApi}=await mod('api/siteContentApi.js');
  const photo={id:1,index:0,is_active:true,translations:[{id:8,locale:'rus',title:'Photo',description:null}]};
  apiClient.get=async()=>photo;
  await siteContentApi.savePhoto('work_photos',1,photo,null);

  const {adminCatalogApi}=await mod('api/adminCatalogApi.js');
  const product={id:1,index:0,name:'Rope',is_active:true,translations:[{id:9,locale:'rus',name:'Rope',description:null,subtitle:null}]};
  const settings={can_be_spliced:true};let writes=0;
  apiClient.get=async endpoint=>endpoint.startsWith('/rope_products/')?settings:product;
  apiClient.patch=apiClient.post=async()=>{writes++;throw Error('Unchanged save must not write');};
  await adminCatalogApi.saveProduct(1,{index:0,is_active:true,translations:[{locale:'rus',name:'Rope',description:null,subtitle:null}],settings});assert.equal(writes,0);
  console.log('PASS: HTTPS configuration, shared isolated configurator data/retry, contacts contract, bounded review requests, unchanged product save');
})().catch(error=>{console.error(error);process.exitCode=1;});
