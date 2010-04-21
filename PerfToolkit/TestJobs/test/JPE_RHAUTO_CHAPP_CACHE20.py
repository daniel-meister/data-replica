# PYTHON configuration file for class: JetPlotsExample
# Description:  Example of simple EDAnalyzer for jets.
# Author: K. Kousouris
# Date:  25 - August - 2008
import FWCore.ParameterSet.Config as cms

process = cms.Process("Ana")
process.load("FWCore.MessageService.MessageLogger_cfi")
#############   Set the number of events #############
process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(50000)
)    

process.source = cms.Source("PoolSource",
                            #                            # replace 'myfile.root' with the source file you want to use
                            fileNames = cms.untracked.vstring('/store/mc/JobRobot/RelValProdTTbar/GEN-SIM-DIGI-RECO/MC_3XY_V24_JobRobot-v1/0001/F218B438-A02C-DF11-AADC-000423D99A8E.root')
                            )

process.source.fileNames = []
mf = open("file.list")
for i in mf:
    i = i.strip("\n")
    process.source.fileNames.append(i)
              

#############   Calo Jets  ###########################
process.calo = cms.EDAnalyzer("CaloJetPlotsExample",
    JetAlgorithm  = cms.string('iterativeCone5CaloJets'),
    HistoFileName = cms.string('JPE_RHAUTO_CHAPP_CACHE20.root'),
    NJets         = cms.int32(2)
)
#############   Path       ###########################
process.p = cms.Path(process.calo)
#############   Format MessageLogger #################
process.MessageLogger.cerr.FwkReport.reportEvery = 100


process.AdaptorConfig = cms.Service("AdaptorConfig",
                                    tempDir=cms.untracked.string(""),
                                    cacheHint=cms.untracked.string("lazy-download"),
                                    readHint=cms.untracked.string("auto-detect"))
process.source.cacheSize = cms.untracked.uint32(20*1024*1024)


process.Timing = cms.Service("Timing",
                             useJobReport = cms.untracked.bool(True)
                             )

#process.CPU = cms.Service("CPU",
#                          useJobReport = cms.untracked.bool(True),
#                          reportCPUProperties = cms.untracked.bool(True)
#                          )
