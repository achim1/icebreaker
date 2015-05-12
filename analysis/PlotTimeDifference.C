#ifndef __CINT__
#include <cstdlib>
#include <iostream>
#include <sstream>
#include "TH1D.h"
#include "TCanvas.h"
#include "TFile.h"
#include "TTree.h"
#include "TPRegexp.h"
#include "TVirtualPad.h"
#include "TF1.h"
#include "TString.h"
#include "TStyle.h"
#include "TColor.h"
#endif

TStyle* set_plot_style(){

    TStyle *my_style = new TStyle("Plain","Plain");
    const int font = 132;

    my_style->SetLabelFont(font, "xyz");
    my_style->SetStatFont(font);
    my_style->SetTitleFont(font, "xyz");
    my_style->SetTitleFont(font, "T");   // T (anything but xyz) --> Pad title
    my_style->SetTextFont(font);
    my_style->SetTitleFontSize(0.035);

    my_style->SetCanvasColor(0);
    my_style->SetTitleFillColor(0);
    my_style->SetStatColor(0);
    my_style->SetHistFillColor(0);
    my_style->SetFrameFillColor(0);
    my_style->SetPadBorderMode(0);
    my_style->SetFrameBorderMode(0);
    //    my_style->SetStatBorderSize(0);
    my_style->SetNumberContours(50);

//    my_style->SetOptStat(""); //No statistics
    my_style->SetOptFit(101); //chi-square and fit parameters
//    my_style->SetOptFit(0); //chi-square and fit parameters
    const Int_t NRGBs = 5;
    const Int_t NCont = 255;

    Double_t stops[NRGBs] = { 0.00, 0.34, 0.61, 0.84, 1.00 };
    Double_t red[NRGBs]   = { 0.00, 0.00, 0.87, 1.00, 0.51 };
    Double_t green[NRGBs] = { 0.00, 0.81, 1.00, 0.20, 0.00 };
    Double_t blue[NRGBs]  = { 0.51, 1.00, 0.12, 0.00, 0.00 };
    TColor::CreateGradientColorTable(NRGBs, stops, red, green, blue, NCont);
    my_style->SetNumberContours(NCont);
    my_style->cd();
    return my_style;
}
void plot_and_fit(TH1D* hists[], TCanvas* c, int histid){
    TVirtualPad* pad = c->cd(histid+1);
    pad->SetLogy();
    TH1D *hist = hists[histid];
    hist->GetXaxis()->SetTitle("#Delta t [s]");
    hist->Draw("HIST");
    TF1 *fa = new TF1(TUUID().AsString(),"[0] * exp(-x * [1])",0,3);
    fa->SetParameter(0,hist->GetSumOfWeights());
    fa->SetParameter(1,2);
    fa->SetParName(0,"Norm1");
    fa->SetParName(1,"Frequency1");
    hist->Fit(fa,"QR");
    fa->Draw("LSAME");
}

TCanvas* PlotTimeDifference(const TString& filename,const double widthcut,const double startfrac, const double endfrac){

#ifndef __CINT__
    TStyle *mystyle = set_plot_style();
#endif
    TH1D* hists[4];
    hists[0] = new TH1D("Channel 0","Channel 0",100,0,6);
    hists[1] = new TH1D("Channel 1","Channel 1",100,0,6);
    hists[2] = new TH1D("Channel 2","Channel 2",100,0,6);
    hists[3] = new TH1D("Channel 3","Channel 2",100,0,6);
    TFile f(filename);
    TTree *tree = (TTree*)f.Get("aTree");
    const size_t nentries = tree->GetEntries();
    double event_sec;
    int channel;
    double width;
    tree->SetBranchAddress("EventSecOfDay",&event_sec);
    tree->SetBranchAddress("ChannelID",&channel);
    tree->SetBranchAddress("PulseWidth",&width);
    double previous_time[4] = {-1.,-1.,-1.,-1.};
    size_t counter = 0;

    for (size_t i = 0; i < nentries; i++){
        tree->GetEntry(i);
        if (width <= widthcut){
            continue;
        }
        if ((event_sec/86400 < startfrac) | (event_sec/86400 > endfrac)){
            continue;
        }
        if (previous_time[channel] > 0) {
            const double dt = event_sec - previous_time[channel]; //Time difference in seconds
            if (dt<0){
                std::cout << "Error: " << dt << " " << channel << std::endl;
                counter++;
            }
            hists[channel]->Fill(dt);
        }
        previous_time[channel] = event_sec;
    }
    std::cout << counter << " negative time differences" << std::endl;
    TCanvas *c = new TCanvas("Time difference","Time difference",1280,1024);
    c->Divide(2,2);

#ifdef __CINT__   
    gStyle->SetOptFit(1);
#endif
    plot_and_fit(hists, c, 0);
    plot_and_fit(hists, c, 1);
    plot_and_fit(hists, c, 2);
    plot_and_fit(hists, c, 3);

    std::stringstream from;
    from << startfrac;
    std::stringstream to;
    to << endfrac;
    std::stringstream cut;
    cut << widthcut;
    TPRegexp beforedot("[a-zA-z0-9_-]*\\.root");
    TString outfilename = "time_difference_" + filename(beforedot) + "_";
    outfilename += TString(cut.str().c_str()) + "_" + TString(from.str().c_str()) + "_" + TString(to.str().c_str()) + ".pdf";
    c->Print(outfilename);
    return c;
}

#ifndef __CINT__
int main(int argc, char** argv){
    double widthcut = 0.0;
    if (argc > 2){
        widthcut = std::atof(argv[2]);
    }
    double startfrac = 0.0;
    if (argc > 3){
        startfrac = std::atof(argv[3]);
    }
    double endfrac = 1.0;
    if (argc > 4){
        endfrac = std::atof(argv[4]);
    }
    PlotTimeDifference(argv[1],widthcut,startfrac,endfrac);
}
#endif
