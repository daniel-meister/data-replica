# This is an example PAT configuration showing the usage of PAT on full sim samples

# Starting with a skeleton process which gets imported with the following line
from PhysicsTools.PatAlgos.patTemplate_cfg import *

# load the standard PAT config
process.load("PhysicsTools.PatAlgos.patSequences_cff")
from PhysicsTools.PatAlgos.tools.coreTools import *
#restrictInputToAOD(process, ['All'])

# note that you can use a bunch of core tools of PAT 
# to taylor your PAT configuration; for a few examples
# uncomment the following lines
#removeMCMatching(process, 'Muons')
#removeAllPATObjectsBut(process, ['Muons'])
#removeSpecificPATObjects(process, ['Electrons', 'Muons', 'Taus'])
restrictInputToAOD(process)
#removeMCMatching(process, 'Muons')
#removeAllPATObjectsBut(process, ['Muons'])
#removeSpecificPATObjects(process, ['Electrons', 'Muons', 'Taus'])

#switch off new tau features introduced in 33X to restore 31X defaults
# new feaures: - shrinkingConeTaus instead of fixedCone ones
#              - TaNC discriminants attached for shrinkingConeTaus
#              - default preselection on cleaningLayer1
from PhysicsTools.PatAlgos.tools.tauTools import *
switchTo31Xdefaults(process)

# load the coreTools of PAT
from PhysicsTools.PatAlgos.tools.jetTools import *
switchJetCollection(process,
                                        cms.InputTag('sisCone5CaloJets'),
                                        doJTA            = True,
                                        doBTagging       = True,
                                        jetCorrLabel     = ('SC5','Calo'),
                                        doType1MET       = True,
                                        genJetCollection = cms.InputTag("sisCone5GenJets"),
                                        doJetID      = False,
                                        jetIdLabel   = "ak5"
                                        )


# let it run
process.p = cms.Path(
    process.patDefaultSequence
)

# In addition you usually want to change the following parameters:
#
#   process.GlobalTag.globaltag =  ...    ##  (according to https://twiki.cern.ch/twiki/bin/view/CMS/SWGuideFrontierConditions)
process.source.fileNames = [
'/store/relval/CMSSW_3_3_2/RelValQCD_Pt_80_120/GEN-SIM-RECO/MC_31X_V9-v2/0000/3A005AC9-58C8-DE11-A2F5-001A9281173A.root'
                            ]
process.AdaptorConfig = cms.Service("AdaptorConfig",
#                                    tempDir=cms.untracked.string(""),
                                    cacheHint=cms.untracked.string("storage-only"),
                                    readHint=cms.untracked.string("auto-detect")
                                    )
process.source.cacheSize = cms.untracked.uint32(20*1024*1024)

#    ]         ##  (e.g. 'file:AOD.root')
process.maxEvents.input = 1000         ##  (e.g. -1 to run on all events)
#   process.out.outputCommands = [ ... ]  ##  (e.g. taken from PhysicsTools/PatAlgos/python/patEventContent_cff.py)
process.out.fileName = 'PAT1_RHAUTO_CHSTO_CACHE20.root'            ##  (e.g. 'myTuple.root')
process.out.outputCommands = cms.untracked.vstring('drop *' )
process.options.wantSummary = False       ##  (to suppress the long output at the end of the job)    
process.MessageLogger.cerr.threshold = 'WARNING'

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

