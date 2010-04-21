// -*- C++ -*-
//
// Package:    MiniTreeReco3
// Class:      MiniTreeReco3
// 
/**\class MiniTreeReco3 MiniTreeReco3.cc Analysis/MiniTreeReco3/src/MiniTreeReco3.cc

 Description: <one line class summary>

 Implementation:
     <Notes on implementation>
*/
//
// Original Author:  Leonardo Sala (ETH) [leo]
//         Created:  Thu Feb 11 14:19:13 CET 2010
// $Id$
//
//


// system include files
#include <memory>

// user include files
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/EDAnalyzer.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"

#include "FWCore/ParameterSet/interface/ParameterSet.h"

#include "FWCore/ParameterSet/interface/InputTag.h"

#include "SimDataFormats/GeneratorProducts/interface/GenEventInfoProduct.h"

#include "FWCore/ServiceRegistry/interface/Service.h"
//#include "PhysicsTools/UtilAlgos/interface/TFileService.h"

#include "SimDataFormats/GeneratorProducts/interface/HepMCProduct.h"

#include "DataFormats/JetReco/interface/GenJet.h"
#include "DataFormats/JetReco/interface/GenJetCollection.h"

#include "DataFormats/JetReco/interface/CaloJet.h"
#include "DataFormats/JetReco/interface/CaloJetCollection.h"

#include "DataFormats/JetReco/interface/PFJetCollection.h"
#include "DataFormats/JetReco/interface/PFJet.h"

#include "DataFormats/EgammaCandidates/interface/GsfElectron.h"
#include "DataFormats/EgammaCandidates/interface/GsfElectronFwd.h"

#include "DataFormats/MuonReco/interface/Muon.h"
#include "DataFormats/MuonReco/interface/MuonFwd.h"

#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/TrackReco/interface/TrackFwd.h"

#include "DataFormats/EgammaCandidates/interface/Photon.h"
#include "DataFormats/EgammaCandidates/interface/PhotonFwd.h"
#include "DataFormats/EgammaReco/interface/BasicCluster.h"
#include "DataFormats/EgammaReco/interface/SuperCluster.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"

#include "DataFormats/GeometryVector/interface/VectorUtil.h" 
#include <CLHEP/Vector/LorentzVector.h>


#include <map>
#include <string>
#include <vector>
#include <iostream>
#include <sstream>


#include "TH1.h"
#include "TH2.h"
#include "TProfile.h"
#include "TRandom.h"
#include "TAxis.h"
#include "TTree.h"
#include "TFile.h"

#include "SimDataFormats/GeneratorProducts/interface/GenEventInfoProduct.h"

#include "PhysicsTools/CandUtils/interface/EventShapeVariables.h"

#define MAXJETS 100
#define MAXPDF 100



using namespace std;

//
// class decleration
//

class MiniTreeReco3 : public edm::EDAnalyzer {
   public:
      explicit MiniTreeReco3(const edm::ParameterSet&);
      ~MiniTreeReco3();


   private:
      virtual void beginJob() ;
      virtual void analyze(const edm::Event&, const edm::EventSetup&);
      virtual void endJob() ;
  float delta_phi(float phi1, float phi2);
  

      // ----------member data ---------------------------

  TFile * m_file;
  TTree * mtree;
  string  rootFile_;


  edm::InputTag JetCollection_;
  edm::InputTag GenJetCollection_;
  edm::InputTag PFJetCollection_;
  const edm::ParameterSet   jetID_;

  std::string JetAlgoLabel_;

  float CaloJetSelection_minPt_, CaloJetSelection_maxEta_,  CaloJetSelection_EMF_, CaloJetSelection_fHPD_, CaloJetSelection_n90Hits_;
  float PFJetSelection_minPt_, PFJetSelection_maxEta_,  PFJetSelection_NHF_, PFJetSelection_NEF_,
    PFJetSelection_CEF_, PFJetSelection_CHF_, PFJetSelection_CM_;

  float MaxPtHat_;

  int PtHatEff;
  int TotalEvts;

  //  int N_PDF;
  //string pdfSet_;
  //double pdfWeights[MAXPDF];
  double pthat;

  double pdf_x1, pdf_x2, pdf_pdf1, pdf_pdf2, pdf_Q;
  int pdf_id1, pdf_id2;

  int nGenJets;
  float GenJet_pt[MAXJETS], GenJet_eta[MAXJETS], GenJet_phi[MAXJETS], GenJet_E[MAXJETS];
  float GenJet_px[MAXJETS], GenJet_py[MAXJETS],GenJet_pz[MAXJETS];

  int nJets;
  int unsel_nJets;

  float HT, PFHT;
};

//
// constants, enums and typedefs
//

//
// static data member definitions
//

//
// constructors and destructor
//
MiniTreeReco3::MiniTreeReco3(const edm::ParameterSet& iConfig){
   //now do what ever initialization is needed
  rootFile_ = iConfig.getParameter<string>("rootfile");

  CaloJetSelection_minPt_ = iConfig.getUntrackedParameter<double>("CaloJetSelection_minPt" );
  CaloJetSelection_maxEta_ = iConfig.getUntrackedParameter<double>("CaloJetSelection_maxEta" );
  CaloJetSelection_EMF_ = iConfig.getUntrackedParameter<double>("CaloJetSelection_EMF" );
  CaloJetSelection_fHPD_ = iConfig.getUntrackedParameter<double>("CaloJetSelection_fHPD" );
  CaloJetSelection_n90Hits_ = iConfig.getUntrackedParameter<double>("CaloJetSelection_n90Hits" );

  PFJetSelection_minPt_ = iConfig.getUntrackedParameter<double>("PFJetSelection_minPt" );
  PFJetSelection_maxEta_= iConfig.getUntrackedParameter<double>("PFJetSelection_maxEta" ); 
  PFJetSelection_NHF_ = iConfig.getUntrackedParameter<double>("PFJetSelection_NHF" );
  PFJetSelection_NEF_ = iConfig.getUntrackedParameter<double>("PFJetSelection_NEF" );
  PFJetSelection_CEF_ = iConfig.getUntrackedParameter<double>("PFJetSelection_CEF" ); 
  PFJetSelection_CHF_= iConfig.getUntrackedParameter<double>("PFJetSelection_CHF" ); 
  PFJetSelection_CM_ = iConfig.getUntrackedParameter<double>("PFJetSelection_CM" );

  MaxPtHat_ = iConfig.getUntrackedParameter<double>("MaxPtHat" );

  JetCollection_ = iConfig.getUntrackedParameter<edm::InputTag>("JetCollection" );
  GenJetCollection_ = iConfig.getUntrackedParameter<edm::InputTag>("GenJetCollection" );
  PFJetCollection_ = iConfig.getUntrackedParameter<edm::InputTag>("PFJetCollection" );

  PtHatEff=0;
  TotalEvts=0;

}


MiniTreeReco3::~MiniTreeReco3(){
}


//
// member functions
//

// ------------ method called to for each event  ------------
void
MiniTreeReco3::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup)
{
   using namespace edm;
   using namespace std;
   //using namespace pat;

   Handle< GenEventInfoProduct > GenInfoHandle;
   iEvent.getByLabel( "generator", GenInfoHandle );
   pthat = ( GenInfoHandle->hasBinningValues() ? 
   		    (GenInfoHandle->binningValues())[0] : 0.0);

   //Handle<double> genEventScale;
   //iEvent.getByLabel( "genEventScale", genEventScale );
   //double pthat2 = *genEventScale;
   /*
   Handle<HepMCProduct> evt;
   iEvent.getByLabel("generator", evt); 
   HepMC::GenEvent * myGenEvent = new  HepMC::GenEvent(*(evt->GetEvent()));
   double pthat = myGenEvent->event_scale();
   delete myGenEvent;
   */
   //PDF systematics
   edm::Handle<GenEventInfoProduct> pdfstuff;
   if (!iEvent.getByLabel("generator", pdfstuff)){
     cout << "argh"<< endl;
     return;
   }

   pdf_Q = pdfstuff->pdf()->scalePDF;
   pdf_id1 = pdfstuff->pdf()->id.first;
   pdf_x1 = pdfstuff->pdf()->x.first;
   pdf_pdf1 = pdfstuff->pdf()->xPDF.first;
   pdf_id2 = pdfstuff->pdf()->id.second;
   pdf_x2 = pdfstuff->pdf()->x.second;
   pdf_pdf2 = pdfstuff->pdf()->xPDF.second; 

   // get jet collection
   //Gen Jets
   
   /////////// Get the jet collection //////////////////////
   Handle<reco::GenJetCollection> genjets;
   iEvent.getByLabel(GenJetCollection_,genjets);
   int index = 0;
   int NJets = (int) genjets->size();
   int myNJet=0;
   for(reco::GenJetCollection::const_iterator i_jet = genjets->begin(); i_jet != genjets->end() && index < NJets; ++i_jet) {
     GenJet_px[myNJet] = i_jet->px();
     GenJet_py[myNJet] = i_jet->py();
     GenJet_pz[myNJet] = i_jet->pz();
     
     GenJet_pt[myNJet] = i_jet->pt();
     GenJet_eta[myNJet] = i_jet->eta();
     GenJet_phi[myNJet] = i_jet->phi();
     GenJet_E[myNJet] = i_jet->energy();
     myNJet++;
   }
   
   
   //Handle< reco::CaloJetCollection > jets;
   //iEvent.getByLabel(JetCollection_,jets);
   //edm::Handle< reco::CaloJet  > jets;
   edm::Handle<edm::View< reco::CaloJet > > jets;
   iEvent.getByLabel(JetCollection_, jets );
   
   string algo =  JetCollection_.label();
   
   //JetID
   // jet ID handle
   nJets=0;
   unsel_nJets=0;
   
   HT=0;
   
   //for( reco::CaloJetCollection::const_iterator jet=jets->begin(); jet!=jets->end(); ++jet){
   
      for ( edm::View<reco::CaloJet>::const_iterator ibegin = jets->begin(),
           iend = jets->end(), jet = ibegin;
         jet != iend; ++jet ){

     
     //jetIDHelper.calculate(iEvent, *jet);
     
     float jetPt = jet->pt();
     float jetEta = jet->eta();

     std::vector<const reco::Candidate*> JetConst = jet->getJetConstituentsQuick ();
     
     HT += jetPt;

     //     for ( reco::CaloJet::const_iterator jet2 = jets->begin(); jet2 = jets->end() && jet!=jet2; ++jet2 ){
     for ( edm::View<reco::CaloJet>::const_iterator ibegin = jets->begin(),
	     iend = jets->end(), jet2 = ibegin;
	   jet2 != iend && jet2!=jet; ++jet2 ){

       float invM = (jet->energy()+jet2->energy())*(jet->energy()+jet2->energy());
       invM -= (jet->px()+jet2->px())*(jet->px()+jet2->px());
       invM -= (jet->py()+jet2->py())*(jet->py()+jet2->py());
       invM -= (jet->pz()+jet2->pz())*(jet->pz()+jet2->pz());
       invM = sqrt(invM);     
     }
     
     ++nJets;
   }
   
     
     //PFJets
   edm::Handle<reco::PFJetCollection> pfJets;
   iEvent.getByLabel(PFJetCollection_, pfJets);
   if(pfJets.isValid()){
     for( reco::PFJetCollection::const_iterator jet=pfJets->begin(); jet!=pfJets->end(); ++jet){
       float jet_pt = jet->pt();
       float jet_eta = jet->eta();
       float jet_px = jet->px();
       float jet_py = jet->py();
       float jet_pz = jet->pz();

       for( reco::PFJetCollection::const_iterator jet2=pfJets->begin(); jet2!=pfJets->end() && jet2!=jet; ++jet2){

	 float invM = (jet->energy()+jet2->energy())*(jet->energy()+jet2->energy());
	 invM -= (jet->px()+jet2->px())*(jet->px()+jet2->px());
	 invM -= (jet->py()+jet2->py())*(jet->py()+jet2->py());
	 invM -= (jet->pz()+jet2->pz())*(jet->pz()+jet2->pz());
	 invM = sqrt(invM);

       }


       if( jet->pt() <= PFJetSelection_minPt_ ) continue;
       if( fabs(jet->eta()) >= PFJetSelection_maxEta_) continue;
       if( jet->neutralHadronEnergyFraction() >= PFJetSelection_NHF_) continue;
       if( jet->neutralEmEnergyFraction() >= PFJetSelection_NEF_) continue;
       if( jet->chargedEmEnergyFraction() >= PFJetSelection_CEF_) continue;
       if(fabs(jet->eta())<2.4 )
	 if( jet->chargedHadronEnergyFraction() <= PFJetSelection_CHF_ || jet->chargedMultiplicity() <= PFJetSelection_CM_ ) continue;
       
       std::vector <reco::PFCandidatePtr> PFConst = jet->getPFConstituents();
       reco::TrackRefVector PFTrackRef = jet->getTrackRefs() ;

     }
   }
   //electrons
   edm::Handle<reco::GsfElectronCollection> gsfElectrons;
   iEvent.getByLabel("gsfElectrons",gsfElectrons);
   for (reco::GsfElectronCollection::const_iterator ele=gsfElectrons->begin();
	ele!=gsfElectrons->end(); ele++){
   
     float ele_pt = ele->pt();
     float ele_eop = ele->eSuperClusterOverP();
     float ele_eseedop = ele->eSeedClusterOverP();
     float ele_detasc = ele->deltaEtaSuperClusterTrackAtVtx();
     double d = ele->vertex().x()*ele->vertex().x()+ele->vertex().y()*ele->vertex().y();

     for (reco::GsfElectronCollection::const_iterator ele2=gsfElectrons->begin();
	  ele2!=gsfElectrons->end() && ele2!=ele; ele2++){
       
       float invM = (ele->energy()+ele2->energy())*(ele->energy()+ele2->energy());
       invM -= (ele->px()+ele2->px())*(ele->px()+ele2->px());
       invM -= (ele->py()+ele2->py())*(ele->py()+ele2->py());
       invM -= (ele->pz()+ele2->pz())*(ele->pz()+ele2->pz());
       invM = sqrt(invM);
     }
     
   }
   

   //Muons
   edm::Handle<reco::MuonCollection> muons;
   iEvent.getByLabel("muons", muons);
   for(reco::MuonCollection::const_iterator muon = muons->begin();
       muon != muons->end(); ++muon){

     float muon_caloComp = muon->caloCompatibility();
     float muon_iso03_sumPt = muon->isolationR03().sumPt;

     for(reco::MuonCollection::const_iterator muon2 = muons->begin();
	 muon2 != muons->end() && muon2!=muon; ++muon2)     {

       float invM = (muon->energy()+muon2->energy())*(muon->energy()+muon2->energy());
       invM -= (muon->px()+muon2->px())*(muon->px()+muon2->px());
       invM -= (muon->py()+muon2->py())*(muon->py()+muon2->py());
       invM -= (muon->pz()+muon2->pz())*(muon->pz()+muon2->pz());
       invM = sqrt(invM);
     }


   }     


   //Tracks
   float sumTrackPt = 0;
   edm::Handle<reco::TrackCollection> tracks;
   iEvent.getByLabel("generalTracks",tracks);
   for(reco::TrackCollection::const_iterator itTrack = tracks->begin(); itTrack != tracks->end(); ++itTrack) {
     const math::XYZVector trackMomentum = itTrack->momentum() ;

     for(reco::TrackCollection::const_iterator itTrack2 = tracks->begin();itTrack2 != tracks->end();++itTrack2) {
       float trkPt2 = itTrack2->pt();
	 const math::XYZVector trackMomentum2 = itTrack2->momentum() ;
	 
	 float dR = ROOT::Math::VectorUtil::DeltaR(trackMomentum, trackMomentum2);
	 if(dR < 0.3 && dR>0.02)
	   sumTrackPt+=trkPt2;
       } 


     const reco::TrackResiduals residuals = itTrack->residuals ();
   }

   Handle<reco::PhotonCollection> photonHandle;
   iEvent.getByLabel("photons", photonHandle);
   const reco::PhotonCollection photonCollection = *(photonHandle.product());
   float photon_rawEnergy=0;
   for( reco::PhotonCollection::const_iterator  iPho = photonCollection.begin(); iPho != photonCollection.end(); iPho++) {
     photon_rawEnergy = iPho->superCluster()->rawEnergy();     

     for( reco::PhotonCollection::const_iterator  iPho2 = photonCollection.begin(); iPho2 != photonCollection.end() && iPho2!=iPho; iPho2++) {

       float invM = (iPho->energy()+iPho2->energy())*(iPho->energy()+iPho2->energy());
       invM -= (iPho->px()+iPho2->px())*(iPho->px()+iPho2->px());
       invM -= (iPho->py()+iPho2->py())*(iPho->py()+iPho2->py());
       invM -= (iPho->pz()+iPho2->pz())*(iPho->pz()+iPho2->pz());
       invM = sqrt(invM);
     }

   }

   // mtree->Fill();

}


// ------------ method called once each job just before starting event loop  ------------
void 
MiniTreeReco3::beginJob()
{
  
}

// ------------ method called once each job just after ending the event loop  ------------
 void MiniTreeReco3::endJob() {
   //m_file->Write();
   //m_file->Close();
}





//define this as a plug-in
DEFINE_FWK_MODULE(MiniTreeReco3);
