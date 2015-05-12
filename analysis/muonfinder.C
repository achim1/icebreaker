#include <cmath>
#include <cstdlib>
#include <list>
#include <map>
#include <iostream>
#include "TString.h"
#include "TTree.h"
#include "TFile.h"

using std::list;
using std::pair;
using std::map;
using std::cout;
using std::endl;

struct Range{

    Range(double from, double to):
        low(from),
        high(to)
    {};
    ~Range(){};

    double low, high;
};

template<class T>
T* find(const map<Range,T*>& histomap, const double val){

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

typedef list<pair<int,double> > pulselist;
typedef map<Range,int*> RangeCounterMap;

bool check_muon(pulselist& pulses){
    bool channels[4] = {false, false, false, false};
    for (pulselist::iterator it = pulses.begin(); it != pulses.end(); ++it){
        channels[it->first] = true;
    }
    return ((channels[0] || channels[1]) && (channels[2] || channels[3]));
}


void clean_pulses(pulselist& pulses, const double maxdt){
    pulselist::iterator it = --pulses.end();
    const double mintime = it->second - maxdt;
    while (it != pulses.begin()){
        pulselist::iterator temp = it;
        --temp;
        if (temp->second < mintime){
            it = pulses.erase(temp);
        }
        else {
            --it;
        }
    }
}

void muonfinder(const TString& filename, const double widthcut, const double muonwindow){
    
    TFile f(filename);
    TTree* tree = (TTree*)f.Get("aTree");
    int channel;
    double secofday, mjd;
    double width;
    tree->SetBranchAddress("ChannelID",&channel);
    tree->SetBranchAddress("EventSecOfDay",&secofday);
    tree->SetBranchAddress("EventTimeMJD",&mjd);
    tree->SetBranchAddress("PulseWidth",&width);
    tree->GetEntry(0);

    pulselist pulses;
    RangeCounterMap hourly;
    for (int i = 0; i <= 23; ++i){
        int *counter = new int;
        *counter = 0;
        hourly[Range(double(i),double(i+1))] = counter;
    }

    long entries = tree->GetEntries();
    for (long i = 1; i < entries; ++i){
        tree->GetEntry(i);
        if (width > widthcut){
            const double hour = secofday/3600;
            int* counter = find(hourly, hour);
            if (!counter){
                continue;
            }
            if (pulses.size() != 0){
                const double lastt = pulses.back().second;
                if (secofday - lastt > muonwindow){
                    clean_pulses(pulses, muonwindow);
                    if (check_muon(pulses)){
                        (*counter)++;
                    }
                    pulses.clear();
                }
            }
            pulses.push_back(std::make_pair(channel,secofday));
            clean_pulses(pulses,muonwindow);
        }
//        std::cout << mjd << std::endl;
    }
    RangeCounterMap::iterator iter(hourly.begin());
    for (;iter != hourly.end();++iter){
        cout << iter->first.low << " " << *iter->second << endl;
    }
}

int main(int argc, char** argv){
    double widthcut = 0;
    if (argc > 2){
        widthcut = std::atof(argv[2]);
    }
    double muonwindow = 200e-9;
    if (argc > 3){
        muonwindow = std::atof(argv[3]) * 1e-9;
    }
    muonfinder(argv[1],widthcut,muonwindow);
}
