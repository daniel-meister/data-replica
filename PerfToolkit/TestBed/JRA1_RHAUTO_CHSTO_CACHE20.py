import FWCore.ParameterSet.Config as cms

#!
#! ADJUST JET & REFERENCE PRESELECTION, RESPONSE ANALYSIS PARAMETERS
#!
import JetMETAnalysis.JetAnalyzers.JRA_Defaults_cff as Defaults;
import JetMETAnalysis.JetAnalyzers.JRA_HistoDefaults_cff as Histos;

Defaults.JetPtEta = cms.PSet(
    etaMin = cms.double(-5.0),
    etaMax = cms.double(5.0),
    ptMin  = cms.double(1.0)
)
Defaults.RefPtEta = cms.PSet(
    etaMin = cms.double(-5.0),
    etaMax = cms.double(5.0),
    ptMin = cms.double(10.0)
)
Defaults.JetResponseParameters = Histos.JetResponseParameters


#
# JRA defaults suitable for validation histograms
#

# pT binning
Defaults.JetResponseParameters.binsPt = cms.vdouble(
    10.,15.,20.,30.,45.,65.,100.,180.,250.,350.,500.,800.
    )

# eta binning
Defaults.JetResponseParameters.binsEta = cms.vdouble(
    0.0,1.4,2.6,3.2,4.7
    )

# absolute response histogram parameters
Defaults.JetResponseParameters.nBinsAbsRsp = cms.uint32(200);
Defaults.JetResponseParameters.absRspMin   = cms.double(-300);
Defaults.JetResponseParameters.absRspMax   = cms.double(100);


#!
#! PROCESS
#!
process = cms.Process("JRA")

process.load("JetMETAnalysis.JetAnalyzers.JRA_TreeDefaults_cff")


#!
#! INPUT
#!
process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(-1))
process.source = cms.Source(
    "PoolSource",
    fileNames = cms.untracked.vstring(
'/store/relval/CMSSW_3_3_2/RelValQCD_Pt_80_120/GEN-SIM-RECO/MC_31X_V9-v2/0000/3A005AC9-58C8-DE11-A2F5-001A9281173A.root'
    )
    )


#!
#! SERVICES
#!
process.MessageLogger = cms.Service("MessageLogger",
    destinations = cms.untracked.vstring('cout'),
    cout         = cms.untracked.PSet(threshold = cms.untracked.string('WARNING'))
)
process.TFileService = cms.Service("TFileService",
    fileName      = cms.string('JRA1_RHAUTO_CHSTO_CACHE20.root'),
    closeFileFast = cms.untracked.bool(True)
)

process.MessageLogger = cms.Service("MessageLogger",
                                    cout = cms.untracked.PSet(
    default = cms.untracked.PSet(
    limit = cms.untracked.int32(10) ## kill all messages in the log
    )#,
    #FwkJob = cms.untracked.PSet(
    #limit = cms.untracked.int32(10) ## but FwkJob category - those unlimited
    #)
    ),
                                    categories = cms.untracked.vstring('FwkJob'),
                                    destinations = cms.untracked.vstring('cout')
                                    )

process.Timing = cms.Service("Timing",
                             useJobReport = cms.untracked.bool(True)
                             )

process.CPU = cms.Service("CPU",
                          useJobReport = cms.untracked.bool(True),
                          reportCPUProperties = cms.untracked.bool(True)
                          )

process.SimpleMemoryCheck = cms.Service("SimpleMemoryCheck",
                                        useJobReport = cms.untracked.bool(True)
                                        )



#process.AdaptorConfig = cms.Service("AdaptorConfig",   enable=cms.untracked.bool(False))
process.source.cacheSize = cms.untracked.uint32(20*1024*1024)
process.AdaptorConfig = cms.Service("AdaptorConfig",
                                    cacheHint=cms.untracked.string("storage-only"),
                                    readHint=cms.untracked.string("auto-detect"))
#process.source.cacheSize = cms.untracked.uint32(20*1024*1024)
#process.AdaptorConfig = cms.Service("AdaptorConfig",
#                                    cacheHint=cms.untracked.string("application-only"),
#                                    readHint=cms.untracked.string("auto-detect")
#                                    )

#!
#! SCHEDULE
#!
process.load("JetMETAnalysis.JetAnalyzers.JRA_Schedules_cff")
process.schedule = cms.Schedule()
process.schedule.extend(process.JRAStandardCaloJetsSchedule)
process.schedule.extend(process.JRAStandardCaloL2L3JetsSchedule)
# process.schedule.extend(process.JRAExtraCaloJetsSchedule)
# process.schedule.extend(process.JRAExtraCaloL2L3JetsSchedule)
process.schedule.extend(process.JRAStandardPFJetsSchedule)
process.schedule.extend(process.JRAStandardPFL2L3JetsSchedule)
# process.schedule.extend(process.JRAExtraPFJetsSchedule)
# process.schedule.extend(process.JRAExtraPFL2L3JetsSchedule)
# process.schedule.extend(process.JRAStandardTrkJetsSchedule)
# process.schedule.extend(process.JRAExtraTrkJetsSchedule)
# process.schedule.extend(process.JRAStandardJPTJetsSchedule)
