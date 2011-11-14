import FWCore.ParameterSet.Config as cms
import FWCore.ParameterSet.VarParsing as VarParsing

process = cms.Process("NTupleProducer")
process.load("FWCore.MessageService.MessageLogger_cfi")
#process.MessageLogger.cerr.threshold = "ERROR"
process.load("Configuration.StandardSequences.Geometry_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
process.load("Configuration.StandardSequences.MagneticField_cff")


############ PF2PAT ##########################################
# load the standard PAT config
process.load("PhysicsTools.PatAlgos.patSequences_cff")
from PhysicsTools.PatAlgos.patEventContent_cff import patEventContent

process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(5000) )

process.source = cms.Source("PoolSource",
                            # replace 'myfile.root' with the source file you want to use
                            fileNames = cms.untracked.vstring(
'/store/mc/SAM/RelValProdTTbar/GEN-SIM-RECO/MC_42_V12_SAM-v1/0092/0ECB8D49-EC94-E011-865E-0018F3D0968A.root',
'/store/mc/SAM/RelValProdTTbar/GEN-SIM-RECO/MC_42_V12_SAM-v1/0092/2A805A6A-C593-E011-8CE7-002618FDA263.root',
'/store/mc/SAM/RelValProdTTbar/GEN-SIM-RECO/MC_42_V12_SAM-v1/0092/E2F302D9-B592-E011-B3E7-0026189438A2.root',
'/store/mc/SAM/RelValProdTTbar/GEN-SIM-RECO/MC_42_V12_SAM-v1/0092/EC6673E0-CA92-E011-9C63-002618FDA21D.root'

    )
                            )


# Add a pro forma output module because PF2PAT complains otherwise...
process.out = cms.OutputModule("PoolOutputModule",
                               # save only events passing the full path
                               SelectEvents   = cms.untracked.PSet( SelectEvents = cms.vstring('p') ),
                               # save PAT Layer 1 output; you need a '*' to
                               outputCommands = cms.untracked.vstring('drop *' )
                               )

# Configure PAT to use PF2PAT instead of AOD sources
from PhysicsTools.PatAlgos.tools.pfTools import *

process.GlobalTag.globaltag = cms.string("START42_V12::All")
#process.GlobalTag.globaltag = cms.string("auto::All")


### Jet Corrections ##########################################################
# See https://twiki.cern.ch/twiki/bin/view/CMS/WorkBookJetEnergyCorrections
# note: this runs the L1Fast-Jet corrections for PF jets. not applied on Calo
process.load('JetMETCorrections.Configuration.DefaultJEC_cff')
process.load('RecoJets.Configuration.RecoPFJets_cff')
# Turn-on the FastJet density calculation -----------------------
process.kt6PFJets.doRhoFastjet = True
# Turn-on the FastJet jet area calculation
process.ak5PFJets.doAreaFastjet = True
process.ak5PFJets.Rho_EtaMax = process.kt6PFJets.Rho_EtaMax


### Configuration in common to all collections
usePF2PAT(process,runPF2PAT=True, jetAlgo='AK5', runOnMC=True)#, postfix='PF2PAT') 
# turn to false when running on data and MC 
#getattr(process, 'patElectrons').embedGenMatch = False
#getattr(process, 'patMuons').embedGenMatch = False


#the dump, just for test (disabled)
process.dump=cms.EDAnalyzer('EventContentAnalyzer')

process.ak5JetTracksAssociatorAtVertex.jets = cms.InputTag("ak5PFJets")

#process.SimpleMemoryCheck = cms.Service("SimpleMemoryCheck")


### TFileAdaptor settings
#process.AdaptorConfig = cms.Service("AdaptorConfig",
#                                    tempDir=cms.untracked.string(""),
#                                    cacheHint=cms.untracked.string("lazy-download"),
#                                    readHint=cms.untracked.string("auto-detect"))
#process.source.cacheSize = cms.untracked.uint32(20*1024*1024)

process.p = cms.Path(
    process.kt6PFJets
    + process.ak5PFJets+
     process.patPF2PATSequence
    #+ process.dump
    )



