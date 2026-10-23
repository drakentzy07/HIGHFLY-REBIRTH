// R16 canonical permanent Core contract. Node v24 TS type stripping runs
// the EXACT donor integration TypeScript module after our source patch.
import assert from 'node:assert/strict';
import test from 'node:test';
import {
  HIGHFLY_AWAKENING_CLASSES, HIGHFLY_CORE_STATS,
  createHighflyHunterProfile, applyHunterProgression,
  allocateTrainingPoints, migrateAwakeningStats,
} from '../src/highfly/training/core.ts';

test('R16 all nine classes: LV1->20 NEVER yields STR/AGI/VIT/PER/INT',()=>{
  for(const cls of HIGHFLY_AWAKENING_CLASSES){
    const start=createHighflyHunterProfile({profileId:'r16:'+cls,classId:cls,level:1});
    const level20=applyHunterProgression(start,{level:20});
    assert.equal(level20.hunter.level,20);
    for(const stat of HIGHFLY_CORE_STATS){
      const before=start.training.core[stat],after=level20.training.core[stat];
      assert.equal(before.naturalLevelGrowth,0,cls+' '+stat+' at LV1');
      assert.equal(after.naturalLevelGrowth,0,cls+' '+stat+' at LV20');
      assert.equal(after.current,before.current,cls+' '+stat+' changed with level');
    }
  }
});
test('R16 only validated Training Points can raise permanent Core',()=>{
  const start=createHighflyHunterProfile({profileId:'r16:training',classId:'warrior'});
  const noTraining=applyHunterProgression(start,{level:20});
  assert.throws(()=>allocateTrainingPoints(noTraining,'STR',1),/available/);
  // Lab fixture represents points earned by the existing protected
  // Performance Gate. Production earnTrainingPoints() is unchanged.
  const wallet={...noTraining.training.points,earned:2,available:2};
  const fixture={...noTraining,training:{...noTraining.training,points:wallet}};
  const raised=allocateTrainingPoints(fixture,'STR',2);
  assert.equal(raised.training.core.STR.current,start.training.core.STR.current+2);
  for(const stat of HIGHFLY_CORE_STATS.filter(s=>s!=='STR')){
    assert.equal(raised.training.core[stat].current,start.training.core[stat].current);
  }
  assert.equal(raised.training.points.available,0);
  assert.equal(raised.training.points.earned,2);
});
test('R16 old LV bonus is not mistaken for Training Points on migration',()=>{
  const profile=createHighflyHunterProfile({profileId:'r16:legacy',classId:'mage',level:20});
  const stale={...profile,training:{...profile.training,core:{...profile.training.core,INT:{
    ...profile.training.core.INT,
    naturalLevelGrowth:5,
    current:profile.training.core.INT.current+5,
  }}}};
  const migrated=migrateAwakeningStats(stale);
  assert.equal(migrated.training.core.INT.naturalLevelGrowth,0);
  assert.equal(migrated.training.core.INT.current,profile.training.core.INT.current);
  assert.equal(migrated.training.points.earned,0);
});
