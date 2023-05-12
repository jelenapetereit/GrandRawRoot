"""
Read/Write python interface to GRAND data (real and simulated) stored in Cern ROOT TTrees.

This is the interface for accessing GRAND ROOT TTrees that do not require the user (reader/writer of the TTrees) to have any knowledge of ROOT. It also hides the internals from the data generator, so that the changes in the format are not concerning the user.
"""

from logging import getLogger
import sys
import datetime
import os

import ROOT
import numpy as np
import glob

from collections import defaultdict

# This import changes in Python 3.10
if sys.version_info.major >= 3 and sys.version_info.minor < 10:
    from collections import MutableSequence
else:
    from collections.abc import MutableSequence
        
from dataclasses import dataclass, field    

thismodule = sys.modules[__name__]

from root_trees import *

###########################################################################################################################################################################################################
#
# RawShowerTree
#
##########################################################################################################################################################################################################


@dataclass
## The class for storing a shower simulation-only data for each event
class RawShowerTree(MotherEventTree):
    """The class for storing a shower simulation-only data for each event"""

    _type: str = "rawshower"

    _tree_name: str = "trawshower"
    
    ## Name and version of the shower simulator
    _shower_sim: StdString = StdString("")

    ### Event name (the task name, can be usefull to track the original simulation)
    _event_name: StdString = StdString("")

    ### Event Date  (used to define the atmosphere and/or the magnetic field)
    _event_date: StdString = StdString("")
    
    ### Unix time of the trigger for this DU
    _unix_date: np.ndarray = field(default_factory=lambda: np.zeros(1, np.uint32))
   
    ### Random seed
    _rnd_seed: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float64))
    
    ### Energy in neutrinos generated in the shower (GeV). Useful for invisible energy computation
    _energy_in_neutrinos: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float32))
    
    ### Primary energy (GeV) 
    _energy_primary: StdVectorList = field(default_factory=lambda: StdVectorList("float"))
    
    ### Shower azimuth (deg, CR convention)
    _azimuth: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float32))

    ### Shower zenith  (deg, CR convention)
    _zenith: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float32))
    
    ### Primary particle type (PDG)
    _primary_type: StdVectorList = field(default_factory=lambda: StdVectorList("string"))

    # Primary injection point [m] in Shower coordinates
    _prim_injpoint_shc: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))

    ### Primary injection altitude [m] in Shower Coordinates
    _prim_inj_alt_shc: StdVectorList = field(default_factory=lambda: StdVectorList("float"))

    # primary injection direction in Shower Coordinates
    _prim_inj_dir_shc: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))

    ### Atmospheric model name TODO:standardize
    _atmos_model: StdString = StdString("")

    # Atmospheric model parameters: TODO: Think about this. Different models and softwares can have different parameters
    _atmos_model_param: np.ndarray = field(default_factory=lambda: np.zeros(3, np.float32))
    
    # Table of air density [g/cm3] and vertical depth [g/cm2] versus altitude [m]
    _atmos_altitude: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))
    _atmos_density: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))
    _atmos_depth: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))

        
    ### Magnetic field parameters: Inclination, Declination, Fmodulus.: In shower coordinates. Declination
    #The Earth’s magnetic field, B, is described by its strength, Fmodulus = ∥B∥; its inclination, I, defined
    # as the angle between the local horizontal plane and the field vector; and its declination, D, defined
    # as the angle between the horizontal component of B, H, and the geographical North (direction of
    # the local meridian). The angle I is positive when B points downwards and D is positive when H is 
    # inclined towards the East.    
    _magnetic_field: np.ndarray = field(default_factory=lambda: np.zeros(3, np.float32))

    ### Shower Xmax depth  (g/cm2 along the shower axis)
    _xmax_grams: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float32))
    
    ### Shower Xmax position in shower coordinates [m]
    _xmax_pos_shc: np.ndarray = field(default_factory=lambda: np.zeros(3, np.float64))
    
    ### Distance of Xmax  [m] to the ground
    _xmax_distance: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float64))
    
    ### Altitude of Xmax  [m]. Its important for the computation of the index of refraction at maximum, and of the cherenkov cone
    _xmax_alt: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float64))

    ### high energy hadronic model (and version) used TODO: standarize
    _hadronic_model: StdString = StdString("")
    
    ### low energy model (and version) used TODO: standarize
    _low_energy_model: StdString = StdString("")
    
    ### Time it took for the simulation of the cascade (s). In the case shower and radio are simulated together, use TotalTime/(nant-1) as an approximation
    _cpu_time: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float32))


    #### ZHAireS/Coreas
    # Thinning energy, relative to primary energy
    _relative_thinning: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float64))

    # Main weight factor parameter. This has different meaning for Coreas and Zhaires
    _weight_factor: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float64))

    #gamma energy cut (GeV)
    _gamma_energy_cut: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float64))

    #electron/positron energy cut (GeV)
    _electron_energy_cut: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float64))

    #muons energy cut (GeV)
    _muon_energy_cut: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float64))

    #mesons energy cut (GeV)
    _meson_energy_cut: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float64))

    #nucleons energy cut (GeV)
    _nucleon_energy_cut: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float64))


    ###META ZHAireS/Coreas

    ### Core position with respect to the antenna array (undefined for neutrinos)
    _shower_core_pos: np.ndarray = field(default_factory=lambda: np.zeros(3, np.float32))
    
 
    ### Longitudinal Pofiles (those compatible between Coreas/ZHAires)
    
    ## Longitudinal Profile of vertical depth (g/cm2)
    _long_depth: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))
    ## Longitudinal Profile of slant depth (g/cm2)
    _long_slantdepth: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))
    ## Longitudinal Profile of Number of Gammas      
    _long_gammas: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))
    ## Longitudinal Profile of Number of e+
    _long_eplus: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))
    ## Longitudinal Profile of Number of e-
    _long_eminus: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>")) 
    ## Longitudinal Profile of Number of mu+
    _long_muplus: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))
    ## Longitudinal Profile of Number of mu-
    _long_muminus: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))      
    ## Longitudinal Profile of Number of All charged particles
    _long_allch: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))   
    ## Longitudinal Profile of Number of Nuclei
    _long_nuclei: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))
    ## Longitudinal Profile of Number of Hadrons
    _long_hadr:StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))

    ## Longitudinal Profile of Energy of created neutrinos (GeV)
    _long_neutrino: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))           


    ## Longitudinal Profile of low energy gammas (GeV)
    _long_gamma_cut: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))           
    ## Longitudinal Profile of low energy e+/e- (GeV)
    _long_e_cut: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))           
    ## Longitudinal Profile of low energy mu+/mu- (GeV)
    _long_mu_cut: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))           
    ## Longitudinal Profile of low energy hadrons (GeV)
    _long_hadr_cut: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))
    
    ## Longitudinal Profile of energy deposit by gammas (GeV)
    _long_gamma_ioniz: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))                          
    ## Longitudinal Profile of energy deposit by e+/e-  (GeV)
    _long_e_ioniz: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))           
    ## Longitudinal Profile of energy deposit by muons  (GeV)
    _long_mu_ioniz: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))           
    ## Longitudinal Profile of energy deposit by hadrons (GeV)
    _long_hadr_ioniz: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))     
 

    @property
    def shower_sim(self):
         return str(self._shower_sim)
    
    @shower_sim.setter
    def shower_sim(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(f"Incorrect type for site {type(value)}. Either a string or a ROOT.std.string is required.")
    
        self._shower_sim.string.assign(value)

    @property
    def long_depth(self):
        """Longitudinal profile depth (g/cm2)"""
        return self._long_depth

    @long_depth.setter
    def long_depth(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_depth.clear()
            self._long_depth += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_depth._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_depth {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )            
        

    @property
    def long_slantdepth(self):
        """Longitudinal profile of slant depth (g/cm2)"""
        return self._long_slantdepth

    @long_slantdepth.setter
    def long_slantdepth(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_slantdepth.clear()
            self._long_slantdepth += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_slantdepth._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_slantdepth {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )
 
    @property
    def long_gammas(self):
        """Longitudinal profile of gammas"""
        return self._long_gammas

    @long_gammas.setter
    def long_gammas(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_gammas.clear()
            self._long_gammas += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_gammas._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_gammas {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )    

    @property
    def long_eplus(self):
        """Longitudinal profile of positrons"""
        return self._long_eplus

    @long_eplus.setter
    def long_eplus(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_eplus.clear()
            self._long_eplus += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_eplus._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_eplus {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )    

    @property
    def long_eminus(self):
        """Longitudinal profile of electrons"""
        return self._long_eminus

    @long_eminus.setter
    def long_eminus(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_eminus.clear()
            self._long_eminus += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_eminus._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_eminus {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )    

    @property
    def long_muplus(self):
        """Longitudinal profile of positrons"""
        return self._long_muplus

    @long_muplus.setter
    def long_muplus(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_muplus.clear()
            self._long_muplus += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_muplus._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_muplus {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )    

    @property
    def long_muminus(self):
        """Longitudinal profile of electrons"""
        return self._long_muminus

    @long_muminus.setter
    def long_muminus(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_muminus.clear()
            self._long_muminus += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_muminus._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_muminus {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )  

    @property
    def long_allch(self):
        """Longitudinal profile of all charged particles"""
        return self._long_allch

    @long_allch.setter
    def long_allch(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_allch.clear()
            self._long_allch += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_allch._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_allch {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )  

    @property
    def long_nuclei(self):
        """Longitudinal profile of nuclei"""
        return self._long_nuclei
        
    @long_nuclei.setter
    def long_nuclei(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_nuclei.clear()
            self._long_nuclei += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_nuclei._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_nuclei {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )  


    @property
    def long_hadr(self):
        """Longitudinal profile of hadrons"""
        return self._long_hadr
        
    @long_hadr.setter
    def long_hadr(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_hadr.clear()
            self._long_hadr += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_hadr._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_hadr {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )  

    @property
    def long_neutrino(self):
        """Longitudinal profile of created neutrinos"""
        return self._long_neutrino
        
    @long_neutrino.setter
    def long_neutrino(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_neutrino.clear()
            self._long_neutrino += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_neutrino._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_neutrino {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )  

    @property
    def long_gamma_cut(self):
        """Longitudinal profile of low energy gammas"""
        return self._long_gamma_cut

    @long_gamma_cut.setter
    def long_gamma_cut(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_gamma_cut.clear()
            self._long_gamma_cut += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_gamma_cut._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_gamma_cut {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )
                
    @property
    def long_gamma_ioniz(self):
        """Longitudinal profile of gamma energy deposit"""
        return self._long_gamma_ioniz

    @long_gamma_ioniz.setter
    def long_gamma_ioniz(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_gamma_ioniz.clear()
            self._long_gamma_ioniz += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_gamma_ioniz._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_gamma_ioniz {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )    
            
    @property
    def long_e_cut(self):
        """Longitudinal profile of low energy e+/e-"""
        return self._long_e_cut

    @long_e_cut.setter
    def long_e_cut(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_e_cut.clear()
            self._long_e_cut += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_e_cut._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_e_cut {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )
                
    @property
    def long_e_ioniz(self):
        """Longitudinal profile of energy deposit by e+/e-"""
        return self._long_e_ioniz

    @long_e_ioniz.setter
    def long_e_ioniz(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_e_ioniz.clear()
            self._long_e_ioniz += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_e_ioniz._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_e_ioniz {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )  

    @property
    def long_mu_cut(self):
        """Longitudinal profile of low energy muons"""
        return self._long_mu_cut

    @long_mu_cut.setter
    def long_mu_cut(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_mu_cut.clear()
            self._long_mu_cut += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_mu_cut._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_mu_cut {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )
                
    @property
    def long_mu_ioniz(self):
        """Longitudinal profile of muon energy deposit"""
        return self._long_mu_ioniz

    @long_mu_ioniz.setter
    def long_mu_ioniz(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_mu_ioniz.clear()
            self._long_mu_ioniz += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_mu_ioniz._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_mu_ioniz {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )
            
    @property
    def long_hadr_cut(self):
        """Longitudinal profile of low energy hadrons"""
        return self._long_hadr_cut

    @long_hadr_cut.setter
    def long_hadr_cut(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_hadr_cut.clear()
            self._long_hadr_cut += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_hadr_cut._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_hadr_cut {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )
                
    @property
    def long_hadr_ioniz(self):
        """Longitudinal profile of hadrons energy deposit"""
        return self._long_hadr_ioniz

    @long_hadr_ioniz.setter
    def long_hadr_ioniz(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._long_hadr_ioniz.clear()
            self._long_hadr_ioniz += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._long_hadr_ioniz._vector = value
        else:
            raise ValueError(
                f"Incorrect type for _long_hadr_ioniz {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )         
  
    @property
    def relative_thinning(self):
        """Thinning energy, relative to primary energy"""
        return self._relative_thinning[0]

    @relative_thinning.setter
    def relative_thinning(self, value: np.float64) -> None:
        self._relative_thinning[0] = value 
 
    @property
    def weight_factor(self):
        """Weight factor"""
        return self._weight_factor[0]

    @weight_factor.setter
    def weight_factor(self, value: np.float64) -> None:
        self._weight_factor[0] = value
 
    @property
    def gamma_energy_cut(self):
        """gamma energy cut (GeV)"""
        return self._gamma_energy_cut[0]

    @gamma_energy_cut.setter
    def gamma_energy_cut(self, value: np.float64) -> None:
        self._gamma_energy_cut[0] = value  
      
    @property
    def electron_energy_cut(self):
        """electron energy cut (GeV)"""
        return self._electron_energy_cut[0]

    @electron_energy_cut.setter
    def electron_energy_cut(self, value: np.float64) -> None:
        self._electron_energy_cut[0] = value 

    @property
    def muon_energy_cut(self):
        """muon energy cut (GeV)"""
        return self._muon_energy_cut[0]

    @muon_energy_cut.setter
    def muon_energy_cut(self, value: np.float64) -> None:
        self._muon_energy_cut[0] = value 

    @property
    def meson_energy_cut(self):
        """meson energy cut (GeV)"""
        return self._meson_energy_cut[0]

    @meson_energy_cut.setter
    def meson_energy_cut(self, value: np.float64) -> None:
        self._meson_energy_cut[0] = value 

    @property
    def nucleon_energy_cut(self):
        """nucleon energy cut (GeV)"""
        return self._nucleon_energy_cut[0]

    @nucleon_energy_cut.setter
    def nucleon_energy_cut(self, value: np.float64) -> None:
        self._nucleon_energy_cut[0] = value 


    @property
    def event_name(self):
        """Event name"""
        return str(self._event_name)

    @event_name.setter
    def event_name(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(
                f"Incorrect type for event_name {type(value)}. Either a string or a ROOT.std.string is required."
            )

        self._event_name.string.assign(value)

    @property
    def event_date(self):
        """Event Date"""
        return str(self._date)

    @event_date.setter
    def event_date(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(
                f"Incorrect type for date {type(value)}. Either a string or a ROOT.std.string is required."
            )

        self._event_date.string.assign(value)

    @property
    def rnd_seed(self):
        """Random seed"""
        return self._rnd_seed[0]

    @rnd_seed.setter
    def rnd_seed(self, value):
        self._rnd_seed[0] = value

    @property
    def energy_in_neutrinos(self):
        """Energy in neutrinos generated in the shower (GeV). Usefull for invisible energy"""
        return self._energy_in_neutrinos[0]

    @energy_in_neutrinos.setter
    def energy_in_neutrinos(self, value):
        self._energy_in_neutrinos[0] = value

    @property
    def energy_primary(self):
        """Primary energy (GeV) TODO: Check unit conventions. # LWP: Multiple primaries? I guess, variable count. Thus variable size array or a std::vector"""
        return self._energy_primary

    @energy_primary.setter
    def energy_primary(self, value):
        # A list of strings was given
        if isinstance(value, list):
            # Clear the vector before setting
            self._energy_primary.clear()
            self._energy_primary += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("float")):
            self._energy_primary._vector = value
        else:
            raise ValueError(
                f"Incorrect type for energy_primary {type(value)}. Either a list or a ROOT.vector of floats required."
            )

    @property
    def azimuth(self):
        """Shower azimuth TODO: Discuss coordinates Cosmic ray convention is bad for neutrinos, but neurtino convention is problematic for round earth. Also, geoid vs sphere problem"""
        return self._azimuth[0]

    @azimuth.setter
    def azimuth(self, value):
        self._azimuth[0] = value

    @property
    def zenith(self):
        """Shower zenith TODO: Discuss coordinates Cosmic ray convention is bad for neutrinos, but neurtino convention is problematic for round earth"""
        return self._zenith[0]

    @zenith.setter
    def zenith(self, value):
        self._zenith[0] = value

    @property
    def primary_type(self):
        """Primary particle type TODO: standarize (PDG?)"""
        return self._primary_type

    @primary_type.setter
    def primary_type(self, value):
        # A list of strings was given
        if isinstance(value, list):
            # Clear the vector before setting
            self._primary_type.clear()
            self._primary_type += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("string")):
            self._primary_type._vector = value
        else:
            raise ValueError(
                f"Incorrect type for primary_type {type(value)}. Either a list or a ROOT.vector of strings required."
            )

    @property
    def prim_injpoint_shc(self):
        """Primary injection point in Shower coordinates"""
        return np.array(self._prim_injpoint_shc)

    @prim_injpoint_shc.setter
    def prim_injpoint_shc(self, value):
        set_vector_of_vectors(value, "vector<float>", self._prim_injpoint_shc, "prim_injpoint_shc")

    @property
    def prim_inj_alt_shc(self):
        """Primary injection altitude in Shower Coordinates"""
        return self._prim_inj_alt_shc

    @prim_inj_alt_shc.setter
    def prim_inj_alt_shc(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._prim_inj_alt_shc.clear()
            self._prim_inj_alt_shc += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("float")):
            self._prim_inj_alt_shc._vector = value
        else:
            raise ValueError(
                f"Incorrect type for prim_inj_alt_shc {type(value)}. Either a list, an array or a ROOT.vector of floats required."
            )

    @property
    def prim_inj_dir_shc(self):
        """primary injection direction in Shower Coordinates"""
        return np.array(self._prim_inj_dir_shc)

    @prim_inj_dir_shc.setter
    def prim_inj_dir_shc(self, value):
        set_vector_of_vectors(value, "vector<float>", self._prim_inj_dir_shc, "prim_inj_dir_shc")

    @property
    def atmos_model(self):
        """Atmospheric model name TODO:standarize"""
        return str(self._atmos_model)

    @atmos_model.setter
    def atmos_model(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(
                f"Incorrect type for site {type(value)}. Either a string or a ROOT.std.string is required."
            )

        self._atmos_model.string.assign(value)

    @property
    def atmos_model_param(self):
        """Atmospheric model parameters: TODO: Think about this. Different models and softwares can have different parameters"""
        return np.array(self._atmos_model_param)

    @atmos_model_param.setter
    def atmos_model_param(self, value):
        self._atmos_model_param = np.array(value).astype(np.float32)
        self._tree.SetBranchAddress("atmos_model_param", self._atmos_model_param)

    @property
    def atmos_altitude(self):
        """height above sea level in meters, for the atmos_density and atmos_depth table"""
        return self._atmos_altitude


    @atmos_altitude.setter
    def atmos_altitude(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._atmos_altitude.clear()
            self._atmos_altitude += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._atmos_altitude._vector = value
        else:
            raise ValueError(
                f"Incorrect type for atmos_altitude {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )            
        
    @property
    def atmos_density(self):
        """Table of air density [g/cm3]"""
        return self._atmos_density
 
    @atmos_density.setter
    def atmos_density(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._atmos_density.clear()
            self._atmos_density += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._atmos_density._vector = value
        else:
            raise ValueError(
                f"Incorrect type for atmos_density {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            ) 
 
        
    @property
    def atmos_depth(self):
        """Table of vertical depth [g/cm2]"""
        return self._atmos_depth
        
    @atmos_depth.setter
    def atmos_depth(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._atmos_depth.clear()
            self._atmos_depth += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._atmos_depth._vector = value
        else:
            raise ValueError(
                f"Incorrect type for atmos_depth {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )




    @property
    def magnetic_field(self):
        """Magnetic field parameters: Inclination, Declination, modulus. TODO: Standarize. Check units. Think about coordinates. Shower coordinates make sense."""
        return np.array(self._magnetic_field)

    @magnetic_field.setter
    def magnetic_field(self, value):
        self._magnetic_field = np.array(value).astype(np.float32)
        self._tree.SetBranchAddress("magnetic_field", self._magnetic_field)

    @property
    def xmax_grams(self):
        """Shower Xmax depth (g/cm2 along the shower axis)"""
        return self._xmax_grams[0]

    @xmax_grams.setter
    def xmax_grams(self, value):
        self._xmax_grams[0] = value

    @property
    def xmax_pos_shc(self):
        """Shower Xmax position in shower coordinates"""
        return np.array(self._xmax_pos_shc)

    @xmax_pos_shc.setter
    def xmax_pos_shc(self, value):
        self._xmax_pos_shc = np.array(value).astype(np.float64)
        self._tree.SetBranchAddress("xmax_pos_shc", self._xmax_pos_shc)

    @property
    def xmax_distance(self):
        """Distance of Xmax [m]"""
        return self._xmax_distance[0]

    @xmax_distance.setter
    def xmax_distance(self, value):
        self._xmax_distance[0] = value

    @property
    def xmax_alt(self):
        """Altitude of Xmax (m, in the shower simulation earth. Its important for the index of refraction )"""
        return self._xmax_alt[0]

    @xmax_alt.setter
    def xmax_alt(self, value):
        self._xmax_alt[0] = value

    @property
    def hadronic_model(self):
        """High energy hadronic model (and version) used TODO: standarize"""
        return str(self._hadronic_model)

    @hadronic_model.setter
    def hadronic_model(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(
                f"Incorrect type for site {type(value)}. Either a string or a ROOT.std.string is required."
            )

        self._hadronic_model.string.assign(value)

    @property
    def low_energy_model(self):
        """High energy model (and version) used TODO: standarize"""
        return str(self._low_energy_model)

    @low_energy_model.setter
    def low_energy_model(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(
                f"Incorrect type for site {type(value)}. Either a string or a ROOT.std.string is required."
            )

        self._low_energy_model.string.assign(value)

    @property
    def cpu_time(self):
        """Time it took for the shower + efield simulation."""
        return np.array(self._cpu_time)

    @cpu_time.setter
    def cpu_time(self, value):
        self._cpu_time = np.array(value).astype(np.float32)
        self._tree.SetBranchAddress("cpu_time", self._cpu_time)
        
    @property
    def shower_core_pos(self):
        """Shower core position"""
        return np.array(self._shower_core_pos)

    @shower_core_pos.setter
    def shower_core_pos(self, value):
        self._shower_core_pos = np.array(value).astype(np.float32)
        self._tree.SetBranchAddress("shower_core_pos", self._shower_core_pos)        
        

    @property
    def unix_date(self):
        """The date of the event in seconds since epoch"""
        return self._run_number[0]

    @unix_date.setter
    def unix_date(self, val: np.uint32) -> None:
        self._unix_date[0] = val



#####################################################################################################################################################################################################
#
# RawEfieldTree
# 
#####################################################################################################################################################################################################
        
@dataclass
## The class for storing Efield simulation-only data common for each event
class RawEfieldTree(MotherEventTree):
    """The class for storing Efield simulation-only data common for each event"""

    _type: str = "rawefield"

    _tree_name: str = "trawefield"

    #Per Event Things
    ## Name and version of the electric field simulator
    _efield_sim: StdString = StdString("")

    ## Name of the atmospheric index of refraction model
    _refractivity_model: StdString = StdString("")
    _refractivity_model_parameters: StdVectorList = field(default_factory=lambda: StdVectorList("double"))    
    _atmos_refractivity: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))
    
    
    ## The antenna time window is defined around a t0 that changes with the antenna, starts on t0+t_pre (thus t_pre is usually negative) and ends on t0+post
    _t_pre: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float32))
    _t_post: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float32))
    _t_bin_size: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float32))    
    
    #Per antenna things
    _du_id: StdVectorList = field(default_factory=lambda: StdVectorList("int"))  # Detector ID
    _du_name: StdVectorList = field(default_factory=lambda: StdVectorList("string"))  # Detector Name
    ## Number of detector units in the event - basically the antennas count
    _du_count: np.ndarray = field(default_factory=lambda: np.zeros(1, np.uint32))


        
    _t_0: StdVectorList = field(default_factory=lambda: StdVectorList("float"))  # Time window t0
    _p2p: StdVectorList = field(default_factory=lambda: StdVectorList("float"))  # peak 2 peak amplitudes (x,y,z,modulus)

    ## X position in shower referential
    _du_x: StdVectorList = field(default_factory=lambda: StdVectorList("float"))
    ## Y position in shower referential
    _du_y: StdVectorList = field(default_factory=lambda: StdVectorList("float"))
    ## Z position in shower referential
    _du_z: StdVectorList = field(default_factory=lambda: StdVectorList("float"))    
    
    ## Efield trace in X direction
    _trace_x: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))
    ## Efield trace in Y direction
    _trace_y: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))
    ## Efield trace in Z direction
    _trace_z: StdVectorList = field(default_factory=lambda: StdVectorList("vector<float>"))



    @property
    def du_count(self):
        """Number of detector units in the event - basically the antennas count"""
        return self._du_count[0]

    @du_count.setter
    def du_count(self, value: np.uint32) -> None:
        self._du_count[0] = value

    @property
    def efield_sim(self):
         return str(self._efield_sim)
    
    @efield_sim.setter
    def efield_sim(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(f"Incorrect type for site {type(value)}. Either a string or a ROOT.std.string is required.")
    
        self._efield_sim.string.assign(value)

    @property
    def refractivity_model(self):
        """Name of the atmospheric index of refraction model"""
        return str(self._refractivity_model)

    @refractivity_model.setter
    def refractivity_model(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(
                f"Incorrect type for site {type(value)}. Either a string or a ROOT.std.string is required."
            )

        self._refractivity_model.string.assign(value)

    @property
    def refractivity_model_parameters(self):
        """Refractivity model parameters"""
        return self._refractivity_model_parameters

    @refractivity_model_parameters.setter
    def refractivity_model_parameters(self, value) -> None:
        # A list of strings was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._refractivity_model_parameters.clear()
            self._refractivity_model_parameters += value
        # A vector was given
        elif isinstance(value, ROOT.vector("double")):
            self._refractivity_model_parameters._vector = value
        else:
            raise ValueError(
                f"Incorrect type for refractivity_model_parameters {type(value)}. Either a list, an array or a ROOT.vector of unsigned shorts required."
            )


    @property
    def atmos_refractivity(self):
        """refractivity for each altitude at atmos_altiude table"""
        return self._atmos_refractivity


    @atmos_refractivity.setter
    def atmos_refractivity(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._atmos_refractivity.clear()
            self._atmos_refractivity += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._atmos_refractivity._vector = value
        else:
            raise ValueError(
                f"Incorrect type for atmos_refractivity {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )            
        

    @property
    def t_pre(self):
        """Starting time of antenna data collection time window. The window starts at t0+t_pre, thus t_pre is usually negative."""
        return self._t_pre[0]

    @t_pre.setter
    def t_pre(self, value):
        self._t_pre[0] = value

    @property
    def t_post(self):
        """Finishing time of antenna data collection time window. The window ends at t0+t_post."""
        return self._t_post[0]

    @t_post.setter
    def t_post(self, value):
        self._t_post[0] = value

    @property
    def t_bin_size(self):
        """Time bin size"""
        return self._t_bin_size[0]

    @t_bin_size.setter
    def t_bin_size(self, value):
        self._t_bin_size[0] = value




    @property
    def du_id(self):
        """Detector ID"""
        return self._du_id

    @du_id.setter
    def du_id(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._du_id.clear()
            self._du_id += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("int")):
            self._du_id._vector = value
        else:
            raise ValueError(
                f"Incorrect type for du_id {type(value)}. Either a list, an array or a ROOT.vector of float required."
            )

    @property
    def du_name(self):
        """Detector Name"""
        return self._du_name    


    @du_name.setter
    def du_name(self, value):
        # A list of strings was given
        if isinstance(value, list):
            # Clear the vector before setting
            self._du_name.clear()
            self._du_name += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("string")):
            self._du_name._vector = value
        else:
            raise ValueError(
                f"Incorrect type for du_name {type(value)}. Either a list or a ROOT.vector of strings required."
            )



    @property
    def t_0(self):
        """Time window t0"""
        return self._t_0

    @t_0.setter
    def t_0(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._t_0.clear()
            self._t_0 += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("float")):
            self._t_0._vector = value
        else:
            raise ValueError(
                f"Incorrect type for t_0 {type(value)}. Either a list, an array or a ROOT.vector of float required."
            )

    @property
    def p2p(self):
        """Peak 2 peak amplitudes (x,y,z,modulus)"""
        return self._p2p

    @p2p.setter
    def p2p(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._p2p.clear()
            self._p2p += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("float")):
            self._p2p._vector = value
        else:
            raise ValueError(
                f"Incorrect type for p2p {type(value)}. Either a list, an array or a ROOT.vector of float required."
            )        

    @property
    def trace_x(self):
        """Efield trace in X direction"""
        return self._trace_x

    @trace_x.setter
    def trace_x(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._trace_x.clear()
            self._trace_x += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._trace_x._vector = value
        else:
            raise ValueError(
                f"Incorrect type for trace_x {type(value)}. Either a list, an array or a ROOT.vector of vector<float> required."
            )

    @property
    def trace_y(self):
        """Efield trace in Y direction"""
        return self._trace_y

    @trace_y.setter
    def trace_y(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._trace_y.clear()
            self._trace_y += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._trace_y._vector = value
        else:
            raise ValueError(
                f"Incorrect type for trace_y {type(value)}. Either a list, an array or a ROOT.vector of float required."
            )

    @property
    def trace_z(self):
        """Efield trace in Z direction"""
        return self._trace_z

    @trace_z.setter
    def trace_z(self, value):
        # A list was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._trace_z.clear()
            self._trace_z += value
        # A vector of strings was given
        elif isinstance(value, ROOT.vector("vector<float>")):
            self._trace_z._vector = value
        else:
            raise ValueError(
                f"Incorrect type for trace_z {type(value)}. Either a list, an array or a ROOT.vector of float required."
            )
        
    @property
    def trace(self):
        """trace info with du_id, traces in all three directions, and time bin stored in one array"""
        return np.concatenate((self._du_id, self._trace_x, self._trace_y, self._trace_z, self.t_bin_size))

    @property
    def du_x(self):
        """X position in site's referential"""
        return self._du_x

    @du_x.setter
    def du_x(self, value) -> None:
        # A list of strings was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._du_x.clear()
            self._du_x += value
        # A vector was given
        elif isinstance(value, ROOT.vector("float")):
            self._du_x._vector = value
        else:
            raise ValueError(
                f"Incorrect type for du_x {type(value)}. Either a list, an array or a ROOT.vector of floats required."
            )

    @property
    def du_y(self):
        """Y position in site's referential"""
        return self._du_y

    @du_y.setter
    def du_y(self, value) -> None:
        # A list of strings was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._du_y.clear()
            self._du_y += value
        # A vector was given
        elif isinstance(value, ROOT.vector("float")):
            self._du_y._vector = value
        else:
            raise ValueError(
                f"Incorrect type for du_y {type(value)}. Either a list, an array or a ROOT.vector of floats required."
            )

    @property
    def du_z(self):
        """Z position in site's referential"""
        return self._du_z

    @du_z.setter
    def du_z(self, value) -> None:
        # A list of strings was given
        if (
            isinstance(value, list)
            or isinstance(value, np.ndarray)
            or isinstance(value, StdVectorList)
        ):
            # Clear the vector before setting
            self._du_z.clear()
            self._du_z += value
        # A vector was given
        elif isinstance(value, ROOT.vector("float")):
            self._du_z._vector = value
        else:
            raise ValueError(
                f"Incorrect type for du_z {type(value)}. Either a list, an array or a ROOT.vector of floats required."
            )


#############################################################################################################################################################################################################################
#
#   RawZHAiresTree
#
#############################################################################################################################################################################################################################
       
@dataclass
## The class for storing shower data for each event specific to ZHAireS only
class RawZHAireSTree(MotherEventTree):
    """The class for storing shower data for each event specific to ZHAireS only"""

    _type: str = "eventshowerzhaires"

    _tree_name: str = "teventshowerzhaires"

    # ToDo: we need explanations of these parameters

    _relative_thining: StdString = StdString("")
    _weight_factor: np.ndarray = field(default_factory=lambda: np.zeros(1, np.float64))
    _gamma_energy_cut: StdString = StdString("")
    _electron_energy_cut: StdString = StdString("")
    _muon_energy_cut: StdString = StdString("")
    _meson_energy_cut: StdString = StdString("")
    _nucleon_energy_cut: StdString = StdString("")
    _other_parameters: StdString = StdString("")

    # def __post_init__(self):
    #     super().__post_init__()
    #
    #     if self._tree.GetName() == "":
    #         self._tree.SetName(self._tree_name)
    #     if self._tree.GetTitle() == "":
    #         self._tree.SetTitle(self._tree_name)
    #
    #     self.create_branches()

    @property
    def relative_thining(self):
        """Relative thinning energy"""
        return str(self._relative_thining)

    @relative_thining.setter
    def relative_thining(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(
                f"Incorrect type for relative_thining {type(value)}. Either a string or a ROOT.std.string is required."
            )

        self._relative_thining.string.assign(value)

    @property
    def weight_factor(self):
        """Weight factor"""
        return self._weight_factor[0]

    @weight_factor.setter
    def weight_factor(self, value: np.float64) -> None:
        self._weight_factor[0] = value

    @property
    def gamma_energy_cut(self):
        """Low energy cut for gammas(GeV)"""
        return str(self._gamma_energy_cut)

    @gamma_energy_cut.setter
    def gamma_energy_cut(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(
                f"Incorrect type for gamma_energy_cut {type(value)}. Either a string or a ROOT.std.string is required."
            )

        self._gamma_energy_cut.string.assign(value)

    @property
    def electron_energy_cut(self):
        """Low energy cut for electrons (GeV)"""
        return str(self._electron_energy_cut)

    @electron_energy_cut.setter
    def electron_energy_cut(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(
                f"Incorrect type for electron_energy_cut {type(value)}. Either a string or a ROOT.std.string is required."
            )

        self._electron_energy_cut.string.assign(value)

    @property
    def muon_energy_cut(self):
        """Low energy cut for muons (GeV)"""
        return str(self._muon_energy_cut)

    @muon_energy_cut.setter
    def muon_energy_cut(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(
                f"Incorrect type for muon_energy_cut {type(value)}. Either a string or a ROOT.std.string is required."
            )

        self._muon_energy_cut.string.assign(value)

    @property
    def meson_energy_cut(self):
        """Low energy cut for mesons (GeV)"""
        return str(self._meson_energy_cut)

    @meson_energy_cut.setter
    def meson_energy_cut(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(
                f"Incorrect type for meson_energy_cut {type(value)}. Either a string or a ROOT.std.string is required."
            )

        self._meson_energy_cut.string.assign(value)

    @property
    def nucleon_energy_cut(self):
        """Low energy cut for nucleons (GeV)"""
        return str(self._nucleon_energy_cut)

    @nucleon_energy_cut.setter
    def nucleon_energy_cut(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(
                f"Incorrect type for nucleon_energy_cut {type(value)}. Either a string or a ROOT.std.string is required."
            )

        self._nucleon_energy_cut.string.assign(value)

    @property
    def other_parameters(self):
        """Other parameters"""
        return str(self._other_parameters)

    @other_parameters.setter
    def other_parameters(self, value):
        # Not a string was given
        if not (isinstance(value, str) or isinstance(value, ROOT.std.string)):
            raise ValueError(
                f"Incorrect type for other_parameters {type(value)}. Either a string or a ROOT.std.string is required."
            )

        self._other_parameters.string.assign(value)        

