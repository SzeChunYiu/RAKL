from __future__ import annotations
import argparse,csv,hashlib,json,re
from pathlib import Path
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression,SGDClassifier
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion

LABELS=('REJECT','CANNOT_CHECK','ACCEPT'); L2I={v:i for i,v in enumerate(LABELS)}
PARENT_EXACT=.5846638655462185
SEED=20260815

def gold_label(e,r):
    if e<=1 and r>=2:return 'ACCEPT'
    if e>=2 or r<=1:return 'REJECT'
    return 'CANNOT_CHECK'
def load_gold(csv_path,ids):
    want=set(map(int,ids));out={}
    with open(csv_path,encoding='utf-8-sig',newline='') as f:
      for i,r in enumerate(csv.DictReader(f)):
        if i in want:out[i]=L2I[gold_label(float(r['entity']),float(r['relation']))]
    assert set(out)==want
    return np.array([out[int(i)] for i in ids],dtype=np.int8)
def load_text(csv_path):
    out={}
    with open(csv_path,encoding='utf-8-sig',newline='') as f:
      for i,r in enumerate(csv.DictReader(f)):out[i]=(r['s1'],r['s2'],r['domain'])
    return out
def loadz(p):
    z=np.load(p);return {k:z[k] for k in z.files}
def vocab_from(z):return sorted(set(map(str,z['domain'])))
def onehot(ds,v):
    pos={d:i for i,d in enumerate(v)};x=np.zeros((len(ds),len(v)),np.float32)
    for i,d in enumerate(ds):
      if str(d) in pos:x[i,pos[str(d)]]=1
    return x
def feat(z,v):
    a=z['e1'].astype(np.float32);b=z['e2'].astype(np.float32)
    return np.concatenate([(a+b)*.5,np.abs(a-b),a*b,np.sum(a*b,axis=1,keepdims=True),onehot(z['domain'],v)],axis=1).astype(np.float32)
def inner(ids):return np.array([int(hashlib.sha256(f'story-v5-inner|{int(i)}'.encode()).hexdigest()[:2],16)<204 for i in ids])
def metrics(y,p):
    y=np.asarray(y);p=np.asarray(p);am=y==2;rm=y==0;cm=y==1;cpm=p==1
    return {'n':len(y),'exact3':float(np.mean(y==p)),'valid_accept':float(np.mean(p[am]==2)),'invalid_false_accept':float(np.mean(p[rm]==2)),'cannot_check_recall':float(np.mean(p[cm]==1)),'cannot_check_precision':float(np.mean(y[cpm]==1)) if cpm.any() else 0.0,'gold_counts':{LABELS[i]:int(np.sum(y==i)) for i in range(3)},'pred_counts':{LABELS[i]:int(np.sum(p==i)) for i in range(3)}}
def safe(m,valid=.55):return m['valid_accept']>=valid-1e-15 and m['invalid_false_accept']<=.15+1e-15
def rank(m):return (m['exact3'],m['cannot_check_recall'],m['valid_accept'],-m['invalid_false_accept'])
def mlp(seed=SEED):return MLPClassifier(hidden_layer_sizes=(256,64),alpha=.001,early_stopping=True,random_state=seed,max_iter=300,batch_size=256,n_iter_no_change=12,validation_fraction=.12)
def lgb():
    from lightgbm import LGBMClassifier
    return LGBMClassifier(n_estimators=500,learning_rate=.05,num_leaves=31,class_weight='balanced',random_state=SEED,verbosity=-1,n_jobs=2)
def fit_three(fam,X,y):
    m=mlp() if fam=='MPNET_THREEWAY_MLP' else lgb();kw={}
    if fam=='MPNET_THREEWAY_MLP':kw['sample_weight']=compute_sample_weight('balanced',y)
    m.fit(X,y,**kw);return m
def fit_factor(X,y,ta=None,trj=None):
    a=(y==2).astype(np.int8);r=(y==0).astype(np.int8);non=y!=2
    ma=mlp(SEED+1);mr=mlp(SEED+2);ma.fit(X,a,sample_weight=compute_sample_weight('balanced',a));mr.fit(X[non],r[non],sample_weight=compute_sample_weight('balanced',r[non]));return ma,mr,ta,trj
def factor_pred(bundle,X,ta,trj):
    ma,mr,_,_=bundle;pa=ma.predict_proba(X)[:,list(ma.classes_).index(1)];pr=mr.predict_proba(X)[:,list(mr.classes_).index(1)];return np.where(pa>=ta,2,np.where(pr>=trj,0,1))
def predict(fam,model,X,spec):
    if fam=='MPNET_FACTORIZED_MLP':return factor_pred(model,X,spec['accept_threshold'],spec['reject_threshold'])
    return model.predict(X)
def train_selected(fam,X,y,spec):return fit_factor(X,y,spec.get('accept_threshold'),spec.get('reject_threshold')) if fam=='MPNET_FACTORIZED_MLP' else fit_three(fam,X,y)

def devcal(args):
    D=loadz(args.emb/'DEV.npz');C=loadz(args.emb/'CALIBRATION.npz');v=vocab_from(D);X=feat(D,v);XC=feat(C,v);y=load_gold(args.csv,D['idx']);yc=load_gold(args.csv,C['idx']);tr=inner(D['idx']);se=~tr
    rows=[]
    for fam in ('MPNET_THREEWAY_MLP','MPNET_THREEWAY_LIGHTGBM'):
      m=fit_three(fam,X[tr],y[tr]);mm=metrics(y[se],m.predict(X[se]));rows.append({'family':fam,'metrics':mm,'joint_safe':safe(mm),'iterations':int(getattr(m,'n_iter_',0))});print(fam,mm,flush=True)
    # factorized two heads, threshold grid fixed by protocol
    a=(y==2).astype(np.int8);r=(y==0).astype(np.int8);non=y!=2;ma=mlp(SEED+1);mr=mlp(SEED+2);ma.fit(X[tr],a[tr],sample_weight=compute_sample_weight('balanced',a[tr]));rr=tr&non;mr.fit(X[rr],r[rr],sample_weight=compute_sample_weight('balanced',r[rr]));pa=ma.predict_proba(X[se])[:,list(ma.classes_).index(1)];pr=mr.predict_proba(X[se])[:,list(mr.classes_).index(1)];best=None
    for ta in np.arange(.35,.751,.05):
      for tj in np.arange(.35,.751,.05):
        p=np.where(pa>=ta,2,np.where(pr>=tj,0,1));mm=metrics(y[se],p)
        if not safe(mm):continue
        key=rank(mm)+(-float(ta),-float(tj))
        if best is None or key>best[0]:best=(key,float(ta),float(tj),mm)
    if best:rows.append({'family':'MPNET_FACTORIZED_MLP','metrics':best[3],'joint_safe':True,'accept_threshold':best[1],'reject_threshold':best[2]})
    else:rows.append({'family':'MPNET_FACTORIZED_MLP','status':'NO_JOINT_SAFE_THRESHOLD','joint_safe':False})
    elig=[r for r in rows if r.get('joint_safe')]
    if not elig:
      out={'terminal':'DEVELOPMENT_NEGATIVE_NO_JOINT_SAFE_PRETRAINED_SEMANTIC_FAMILY','inner':rows,'confirmatory_labels_accessed':False};Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');return
    sel=max(elig,key=lambda q:rank(q['metrics']));fam=sel['family'];spec=dict(sel);model=train_selected(fam,X,y,spec);pc=predict(fam,model,XC,spec);mc=metrics(yc,pc);g={'exact_gt_parent':mc['exact3']>PARENT_EXACT,'gain_ge_0_01':mc['exact3']-PARENT_EXACT>=.01-1e-15,'valid_accept_ge_0_5':mc['valid_accept']>=.5-1e-15,'false_accept_le_0_15':mc['invalid_false_accept']<=.15+1e-15}
    # hostile controls on CAL
    rng=np.random.default_rng(SEED+101);z={k:C[k].copy() for k in C};z['e1']=C['e1'][rng.permutation(len(C['e1']))];z['e2']=C['e2'][rng.permutation(len(C['e2']))];md=metrics(yc,predict(fam,model,feat(z,v),spec));drop=mc['exact3']-md['exact3']
    rng=np.random.default_rng(SEED+102);zg={k:C[k].copy() for k in C}
    for k in ('e1','e2'):
      q=rng.normal(size=C[k].shape).astype(np.float32);q/=np.linalg.norm(q,axis=1,keepdims=True)+1e-12;zg[k]=q
    mg=metrics(yc,predict(fam,model,feat(zg,v),spec))
    dx=onehot(D['domain'],v);dc=onehot(C['domain'],v);dm=LogisticRegression(max_iter=1000,class_weight='balanced',random_state=SEED).fit(dx,y);mdom=metrics(yc,dm.predict(dc))
    yp=y[np.random.default_rng(SEED+103).permutation(len(y))];pm=train_selected(fam,X,yp,spec);mp=metrics(yc,predict(fam,pm,XC,spec))
    fals={'independent_story_permutation':{'exact_drop':drop,'pass':drop>=.10-1e-15,'metrics':md},'gaussian_embeddings':{'pass':not safe(mg,.5),'metrics':mg},'domain_only':{'pass':not (mdom['exact3']>PARENT_EXACT and safe(mdom,.5)),'metrics':mdom},'label_permutation':{'pass':not safe(mp,.5),'metrics':mp}}
    ok=all(g.values()) and all(x['pass'] for x in fals.values());out={'schema_version':'story-v10-devcal-result-v1','terminal':'READY_FOR_CONFIRMATORY_V10' if ok else 'DEVELOPMENT_NEGATIVE_V10_CALIBRATION_OR_FALSIFIER_FAILED','selected_spec':spec,'inner':rows,'calibration':mc,'frozen_parent_exact3':PARENT_EXACT,'calibration_gain':mc['exact3']-PARENT_EXACT,'calibration_gates':g,'falsifiers':fals,'all_falsifiers_pass':all(x['pass'] for x in fals.values()),'confirmatory_labels_accessed':False,'feature_dim':X.shape[1],'domains':v};Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2),flush=True)

def pair_surface(a,b):
    def dg(s):return hashlib.sha256(re.sub(r'[ \t\r\n]+',' ',s.strip()).encode()).hexdigest()
    if dg(a)>dg(b):a,b=b,a
    return f'STORY_A\n{a}\nSTORY_B\n{b}'
def direct_predict(proba,classes,tau):
    classes=np.asarray(classes,dtype=int);arg=np.argmax(proba,axis=1);cls=classes[arg];conf=proba[np.arange(len(proba)),arg];return np.where((cls==1)|(conf>=tau),cls,1)
def choose_direct(proba,classes,y):
    best=None
    for tau in [.50,.55,.60,.65,.70,.75,.80,.85,.90]:
      p=direct_predict(proba,classes,tau);m=metrics(y,p);key=(m['exact3'],-m['invalid_false_accept'],m['valid_accept'],-tau)
      if best is None or key>best[0]:best=(key,tau,p,m)
    return best[1:]
def bootstrap(a,b,reps=10000):
    d=a.astype(float)-b.astype(float);rng=np.random.default_rng(20260814991);v=np.empty(reps)
    for i in range(reps):v[i]=np.mean(d[rng.integers(0,len(d),len(d))])
    return float(np.mean(d)),[float(np.quantile(v,.025)),float(np.quantile(v,.975))]
def confirm(args):
    freeze=json.load(open(args.freeze));assert freeze['selected_spec'];spec=freeze['selected_spec'];fam=spec['family'];D=loadz(args.emb/'DEV.npz');C=loadz(args.emb/'CALIBRATION.npz');Q=loadz(args.emb/'CONFIRMATORY.npz');v=vocab_from(D);X=feat(D,v);XQ=feat(Q,v);y=load_gold(args.csv,D['idx']);yc=load_gold(args.csv,C['idx']);yq=load_gold(args.csv,Q['idx']);model=train_selected(fam,X,y,spec);pq=predict(fam,model,XQ,spec);mq=metrics(yq,pq)
    # exact frozen direct-text parent: fit DEV, choose tau CAL, then predict confirm
    texts=load_text(args.csv);sur=lambda ids:[pair_surface(texts[int(i)][0],texts[int(i)][1]) for i in ids];vec=FeatureUnion([('word',TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True,max_features=120000,lowercase=True)),('char',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,sublinear_tf=True,max_features=120000,lowercase=True))]);XD=vec.fit_transform(sur(D['idx']));XC=vec.transform(sur(C['idx']));XQQ=vec.transform(sur(Q['idx']));parent=SGDClassifier(loss='log_loss',alpha=1e-5,max_iter=2000,tol=1e-4,random_state=20260814,class_weight='balanced').fit(XD,y);tau,pcal,mcal=choose_direct(parent.predict_proba(XC),parent.classes_,yc);assert abs(mcal['exact3']-PARENT_EXACT)<1e-12,(mcal,tau);pp=direct_predict(parent.predict_proba(XQQ),parent.classes_,tau);mp=metrics(yq,pp);point,ci=bootstrap(pq==yq,pp==yq);gate={'n_min':len(yq)>=1000,'gain_ge_0_02':point>=.02-1e-15,'ci_lower_gt_0':ci[0]>0,'valid_accept_ge_0_65':mq['valid_accept']>=.65-1e-15,'false_accept_le_0_15':mq['invalid_false_accept']<=.15+1e-15,'cannot_check_recall_ge_0_4':mq['cannot_check_recall']>=.4-1e-15,'falsifiers_frozen_pass':bool(freeze['all_falsifiers_pass'])};term='PRETRAINED_SEMANTIC_RESIDUAL_SUPPORTED_FRESH_STORYANALOGY' if all(gate.values()) else 'PRETRAINED_SEMANTIC_NO_CONFIRMATORY_RESIDUAL';out={'schema_version':'story-v10-confirmatory-result-v1','terminal':term,'selected_spec':spec,'candidate':mq,'parent':mp,'parent_tau':tau,'paired_exact3_advantage':point,'bootstrap_95ci':ci,'gates':gate,'confirmatory_labels_accessed':True,'n_confirmatory':len(yq),'grants_scientific_authority':False};Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['devcal','confirm']);p.add_argument('--emb',type=Path,default=Path('embeddings'));p.add_argument('--csv',type=Path,default=Path('StoryAnalogy.csv'));p.add_argument('--out',default='V10_RESULT.json');p.add_argument('--freeze',default='V10_FINAL_FREEZE.json');a=p.parse_args();devcal(a) if a.mode=='devcal' else confirm(a)
