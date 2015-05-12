#include <cstdlib>
#include <iostream>
#include <sstream>
#include <map>
#include "TH1D.h"
#include "TFile.h"
#include "TTree.h"
#include "TPRegexp.h"
#include "TVirtualPad.h"
#include "TF1.h"
#include "TString.h"
#include "TStyle.h"
#include "TColor.h"
#include "TCanvas.h"

using namespace std;

TF1* fit(TH1D* hist){
    TCanvas c;
    TF1 *fa = new TF1(TUUID().AsString(),"[0] * exp(-x * [1])",0,3);
    fa->SetParameter(0,hist->GetSumOfWeights());
    fa->SetParameter(1,2);
    fa->SetParName(0,"Norm1");
    fa->SetParName(1,"Frequency1");
    hist->Fit(fa,"QR");
    return fa;
}

struct Range{

    Range(double from, double to):
        low(from),
        high(to)
    {};
    ~Range(){};

    double low, high;
};

template<class T>
T* find_hist(const map<Range,T*>& histomap, const double val){

    typename map<Range,T*>::const_iterator it = histomap.begin();
    typename map<Range,T*>::const_iterator end = histomap.end();
    for (;it != end; ++it){
        if ( (val >= it->first.low) && (val <= it->first.high)){
            return it->second;
        }
    }
    return 0;
}

bool operator<(const Range& a, const Range& b){
    return a.low < b.low;
}

typedef map<Range,TH1D**> RangeHistoMap;

void TimeDifference(const TString& filename, const double widthcut){

    RangeHistoMap hourly;
    for (int i = 0; i <= 23; ++i){
        TH1D** hists = new TH1D*[4];
        hists[0] = new TH1D(TUUID().AsString(),TUUID().AsString(),100,0,6);
        hists[1] = new TH1D(TUUID().AsString(),TUUID().AsString(),100,0,6);
        hists[2] = new TH1D(TUUID().AsString(),TUUID().AsString(),100,0,6);
        hists[3] = new TH1D(TUUID().AsString(),TUUID().AsString(),100,0,6);
        hourly[Range(double(i),double(i+1))] = hists;
    }

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
        const double hour = event_sec/3600;
        TH1D** hists = find_hist(hourly, hour);
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
    RangeHistoMap::iterator iter(hourly.begin());
    cout << "Hour,";
    cout << "Events_ch0,Norm_ch0,Frequency_ch0,ChiSquare_ch0,";
    cout << "Events_ch1,Norm_ch1,Frequency_ch1,ChiSquare_ch1,";
    cout << "Events_ch2,Norm_ch2,Frequency_ch2,ChiSquare_ch2,";
    cout << "Events_ch3,Norm_ch3,Frequency_ch3,ChiSquare_ch3" << endl;
    for (;iter != hourly.end();++iter){
        TH1D** hist = iter->second;
        TF1* f0 = fit(hist[0]);
        TF1* f1 = fit(hist[1]);
        TF1* f2 = fit(hist[2]);
        TF1* f3 = fit(hist[3]);
        cout << iter->first.low << ",";

        cout << hist[0]->GetSumOfWeights() << ",";
        cout << f0->GetParameter(0) << ",";
        cout << f0->GetParameter(1) << ",";
        cout << f0->GetChisquare()/f0->GetNDF() << ",";

        cout << hist[1]->GetSumOfWeights() << ",";
        cout << f1->GetParameter(0) << ",";
        cout << f1->GetParameter(1) << ",";
        cout << f1->GetChisquare()/f1->GetNDF() << ",";

        cout << hist[2]->GetSumOfWeights() << ",";
        cout << f2->GetParameter(0) << ",";
        cout << f2->GetParameter(1) << ",";
        cout << f2->GetChisquare()/f1->GetNDF() << ",";

        cout << hist[3]->GetSumOfWeights() << ",";
        cout << f3->GetParameter(0) << ",";
        cout << f3->GetParameter(1) << ",";
        cout << f3->GetChisquare()/f1->GetNDF();
        cout << endl;
    }
}

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
    TimeDifference(argv[1],widthcut);
}
