import FWCore.ParameterSet.Config as cms

process = cms.Process("miniTreeReco")

process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.threshold = "WARNING"

process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(10) )

process.source = cms.Source("PoolSource",
#                            # replace 'myfile.root' with the source file you want to use
                            fileNames = cms.untracked.vstring('/store/mc/JobRobot/RelValProdTTbar/GEN-SIM-DIGI-RECO/MC_3XY_V24_JobRobot-v1/0001/F218B438-A02C-DF11-AADC-000423D99A8E.root')
#                                                        
)

process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
process.GlobalTag.globaltag = 'START310_V4::All'


process.demo = cms.EDAnalyzer('MiniTreeReco3',
                              JetCollection      = cms.untracked.InputTag("ak5CaloJets"),#,"cleanLayer1JetsPFc","cleanLayer1JetsSC5"),
                              GenJetCollection      = cms.untracked.InputTag("ak5GenJets"),#,"cleanLayer1JetsPFc","cleanLayer1JetsSC5"),
                              PFJetCollection      = cms.untracked.InputTag("ak5PFJets"),#,"cleanLayer1JetsPFc","cleanLayer1JetsSC5"),
                              
                              
                              isMonteCarlo       = cms.untracked.bool(True),
                              MaxPtHat = cms.untracked.double(100000),
                              CaloJetSelection_minPt = cms.untracked.double(10),
                              CaloJetSelection_maxEta = cms.untracked.double(3),
                              CaloJetSelection_EMF = cms.untracked.double(0.01),
                              CaloJetSelection_fHPD = cms.untracked.double(0.98),
                              CaloJetSelection_n90Hits = cms.untracked.double(1),
                              
                              PFJetSelection_minPt = cms.untracked.double(8),
                              PFJetSelection_maxEta= cms.untracked.double(3),
                              PFJetSelection_NHF= cms.untracked.double(0.9),
                              PFJetSelection_NEF= cms.untracked.double(0.9),
                              PFJetSelection_CEF= cms.untracked.double(1.0),
                              PFJetSelection_CHF= cms.untracked.double(0.0),
                              PFJetSelection_CM= cms.untracked.double(0.0),
                              
                              pdfSet = cms.untracked.string("cteq65.LHgrid"),

                              rootfile = cms.string("MTR3.root"),

                              )


process.MessageLogger = cms.Service("MessageLogger",
                                    cout = cms.untracked.PSet(
    default = cms.untracked.PSet(
    reportEvery = cms.untracked.int32(100)## kill all messages in the log
    #limit = cms.untracked.int32(100)
    )#,
    ),
                                    categories = cms.untracked.vstring('FwkJob'),
                                    destinations = cms.untracked.vstring('cout')
                                    )


process.Timing = cms.Service("Timing",
                             useJobReport = cms.untracked.bool(True)
                             )

#process.CPU = cms.Service("CPU",
#                          useJobReport = cms.untracked.bool(True),
#                          reportCPUProperties = cms.untracked.bool(True)
#                          )


#process.AdaptorConfig = cms.Service("AdaptorConfig",
#                                    tempDir=cms.untracked.string(""),
#                                    cacheHint=cms.untracked.string("lazy-download"),
#                                    readHint=cms.untracked.string("auto-detect"))
#process.source.cacheSize = cms.untracked.uint32(20*1024*1024)


#process.myrecoJets = cms.Path(process.recoJets)
#process.schedule = cms.Schedule(process.myrecoJets)

process.p = cms.Path(                     process.demo)
