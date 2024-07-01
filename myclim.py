import random
import xarray as xr
import numpy as np
import sys
#
#-----------------------------------------------------
#--routine to initialise the AOD response to emissions
#-----------------------------------------------------
def initialise_aod_responses():
   #--location of S3A data
   #dirin="/thredds/tgcc/store/oboucher/S3A/"
   #dirin="../GCMdata/"
   dirin="/Users/krishthe1nonly/Downloads/for-files/"
   #--experiments 
   exps=['eq','15S','15N','30S','30N','60S','60N']
   #--pulse injection 
   nbmthinyr=12 #--number of months in yr
   #--initialisations
   aod_strat_sh={}
   aod_strat_nh={}
   nbyr_irf={}
   #--reference experiment
   exp='ref'
   file=dirin+'LMDZOR-S3A-'+exp+'_19950101_20041231_1M_od550_STRAT.nc'
   print(file)
   xrfile=xr.open_dataset(file)
   lons=xrfile.lon
   lats=xrfile.lat
   #--select SH and NH latitudes
   lats_nh=lats[np.where(lats>=0.0)]
   lats_sh=lats[np.where(lats<=0.0)]
   #--length of pulse experiment (in yr)
   nbyr_irf[exp]=len(xrfile.time_counter)//nbmthinyr
   #--select and hemispherically-average AOD for ref experiment
   aod_ref_strat_sh=np.average(xrfile.sel(lat=lats_sh)['od550_STRAT'].values,axis=(1,2))
   aod_ref_strat_nh=np.average(xrfile.sel(lat=lats_nh)['od550_STRAT'].values,axis=(1,2))
   #--prepare AOD time series for 10 GtS injection experiments for 1 yr
   for exp in exps: 
      if exp == '60S' or exp == '60N':
        file=dirin+'LMDZOR-S3A-'+exp+'_19950101_20001231_1M_od550_STRAT.nc'
      else:
        file=dirin+'LMDZOR-S3A-'+exp+'_19950101_20041231_1M_od550_STRAT.nc'
      xrfile=xr.open_dataset(file)
      nbmth=len(xrfile.time_counter)
      nbyr_irf[exp]=len(xrfile.time_counter)//nbmthinyr
      aod_strat_sh[exp]=np.maximum(0,np.average(xrfile.sel(lat=lats_sh)['od550_STRAT'].values,axis=(1,2))-aod_ref_strat_sh[0:nbmth])
      aod_strat_nh[exp]=np.maximum(0,np.average(xrfile.sel(lat=lats_nh)['od550_STRAT'].values,axis=(1,2))-aod_ref_strat_nh[0:nbmth])
   #
   #--compute annual means
   for exp in exps: 
      aod_strat_sh[exp]=np.average(aod_strat_sh[exp].reshape((nbyr_irf[exp],nbmthinyr)),axis=1)
      aod_strat_nh[exp]=np.average(aod_strat_nh[exp].reshape((nbyr_irf[exp],nbmthinyr)),axis=1)
   #
   #--return responses
   return aod_strat_sh, aod_strat_nh, nbyr_irf
#
#-----------------------------------------------------------------
#--routine to convolve emissions with IRF to produce SH and NH AOD
#-----------------------------------------------------------------
def emi2aod(emits,aod_strat_sh,aod_strat_nh,nbyr_irf):
    #--emits: dictionary with emissions counted negative
    #--GtS injected in pulse experiments
    #--as emi are negative by construction, we use a negative emi0 to correct the sign
    emi0=-10.0    
    #--initialise
    AOD_SH=0.0 ; AOD_NH=0.0
    #--check length of time series of emissions
    for exp in emits.keys():
       yrend=nbyr_irf[exp]
       yrend=min(yrend,len(emits[exp])) #--length (in yrs) of past injection time series
    #--loop on experiments
    for exp in emits.keys():
       #--loop on time series, only consider last nbyr years
       for yr,emi in enumerate(emits[exp][-nbyr_irf[exp]:]):     
           #--AODs by summing on injection points and years by convolving with IRF
           AOD_SH += aod_strat_sh[exp][yrend-1-yr]*emi/emi0
           AOD_NH += aod_strat_nh[exp][yrend-1-yr]*emi/emi0
    return AOD_SH, AOD_NH
#
#--------------------------------------
#--routine to compute RF from emissions
#--------------------------------------
def emi2rf(emits,aod_strat_sh,aod_strat_nh,nbyr_irf,aod2rf_sh=-10.0,aod2rf_nh=-10.0):
    aod_sh, aod_nh = emi2aod(emits,aod_strat_sh,aod_strat_nh,nbyr_irf)
    return aod_sh*aod2rf_sh, aod_nh*aod2rf_nh
#
#--------------------------------
#--routine to compute AOD from RF
#--------------------------------
def rf2aod(g,aod2rf_hem=-10.0):
    #--Kleinschmitt et al ACP (2018)
    #-- -10 Wm-2 per unit AOD on average, less in the NH because of surface albedo
    return g/aod2rf_hem
#
#--------------------------------
#--routine to compute AOD from RF
#--------------------------------
def aod2rf(aod,aod2rf_hem=-10.0):
    #--Kleinschmitt et al ACP (2018)
    #-- -10 Wm-2 per unit AOD on average, less in the NH because of surface albedo
    return aod*aod2rf_hem
#
#----------------
#--monsoon precip 
#----------------
def Monsoon(AOD_SH,AOD_NH,noise):
    #--Roose et al., Climate Dynamics, 2023, https://doi.org/10.1007/s00382-023-06799-3
    #--precip change in % as a function of the interhemispheric difference in AOD
    precip_change=-78.6*(AOD_NH-AOD_SH)-10.6 + noise
    return precip_change
#
def Monsoon_IPSL(AOD_SH,AOD_NH,T_SH,T_NH,noise):
    #--fit to IPSL model
    #--precip change in % as a function of the interhemispheric difference in AOD and T
    precip_change=-18.46*(AOD_NH-AOD_SH)+1.24*(T_NH-T_SH) + noise
    return precip_change
#
#----------------------------
#--simple climate NH/SH model
#----------------------------
def clim_sh_nh(Tsh,Tnh,T0sh,T0nh,emits,aod_strat_sh,aod_strat_nh,nbyr_irf, \
               f=1.,geff=1.,tau_nh_sh_upper=10.,tau_nh_sh_lower=20., \
               C=7.,C0=100.,lam=1.,gamma=0.7, ndt=10, Tnh_noise=0, Tsh_noise=0):
# simple climate model from Eq 1 and 2 in Geoffroy et al 
# https://journals.ametsoc.org/doi/pdf/10.1175/JCLI-D-12-00195.1
# Tnh,Tsh = surface air temperature anomaly in K 
# T0nh,T0sh = ocean temperature anomaly in K
# emits = dictionary of past years of strat aerosol emissions (counted negative)
# aod_strat_sh = IRF to convert emissions into SH AOD
# aod_strat_nh = IRF to convert emissions into NH AOD
# f = global GHG forcing in Wm-2 
# geff = efficacy of SRM forcing 
# lam = lambda = feedback parameter Wm-2K-1
# gamma = heat exchange coefficient in Wm-2K-1
# tau_nh_sh_upper = timescale (yrs) of interhemispheric heat transfer for upper ocean layer
# tau_nh_sh_lower = timescale (yrs) of interhemispheric heat transfer for deep ocean layer
# C = atmosphere/land/upper-ocean heat capacity 
# C0 = deep-ocean heat capacity in W.yr.m-2.K-1
# ndt = number of timesteps in 1 yr
# dt = timestep in yr
# noise = noise in T - needs to put a more realistic climate noise
# also noise is only on Tf, should we put noise on T0f as well ?
# gnh,gsh = applied hemispheric SRM forcing in Wm-2
#
  gsh,gnh=emi2rf(emits,aod_strat_sh,aod_strat_nh,nbyr_irf)
  #--test sign geff 
  if geff<0:
      sys.exit('SRM efficacy geff has to be a positive number')
  #--discretize yearly timestep
  dt = 1./float(ndt)
  #--initial T and TO
  Ti_sh = Tsh ; T0i_sh = T0sh
  Ti_nh = Tnh ; T0i_nh = T0nh
  #--ocean fractions (NH/SH/globe)
  ocf_nh=0.6
  ocf_sh=0.8
  ocf=(ocf_sh+ocf_nh)/2.
  # time loop
  for i in range(ndt):
     #--sh, accounting for the larger ocean fraction in SH
     Tf_sh  = Ti_sh + dt/(C*ocf_sh/ocf)*(f+geff*gsh-lam*Ti_sh-gamma*(Ti_sh-T0i_sh))
     T0f_sh = T0i_sh + dt/(C0*ocf_sh/ocf)*gamma*(Ti_sh-T0i_sh)
     #--nh, accounting for the smaller ocean fraction in NH
     Tf_nh  = Ti_nh + dt/(C*ocf_nh/ocf)*(f+geff*gnh-lam*Ti_nh-gamma*(Ti_nh-T0i_nh))
     T0f_nh = T0i_nh + dt/(C0*ocf_nh/ocf)*gamma*(Ti_nh-T0i_nh)
     #--reducing inter-hemispheric T gradient
     dT  = Tf_nh - Tf_sh
     dT0 = T0f_nh - T0f_sh
     Tf_sh = Tf_sh + dt/tau_nh_sh_upper * dT
     Tf_nh = Tf_nh - dt/tau_nh_sh_upper * dT
     T0f_sh = T0f_sh + dt/tau_nh_sh_lower * dT0
     T0f_nh = T0f_nh - dt/tau_nh_sh_lower * dT0
     #--preparing for next time substep
     Ti_sh  = Tf_sh 
     T0i_sh = T0f_sh
     Ti_nh  = Tf_nh 
     T0i_nh = T0f_nh
  # add noise on final Tf
  Tf_sh = Tf_sh + Tsh_noise
  Tf_nh = Tf_nh + Tnh_noise
  # GMST 
  Tf = (Tf_sh+Tf_nh)/2.
  #--return outputs
  return Tf, Tf_sh, Tf_nh, T0f_sh, T0f_nh, gsh, gnh
#
#------------------------------------
#--simple climate NH/SH model from RF
#------------------------------------
def clim_sh_nh_from_rf(Tsh,Tnh,T0sh,T0nh,gsh,gnh,\
               f=1.,geff=1.,tau_nh_sh_upper=20.,tau_nh_sh_lower=20., \
               C=7.,C0=100.,lam=1.,gamma=0.7, ndt=10, Tnh_noise=0, Tsh_noise=0):
# simple climate model from Eq 1 and 2 in Geoffroy et al 
# https://journals.ametsoc.org/doi/pdf/10.1175/JCLI-D-12-00195.1
# Tnh,Tsh = surface air temperature anomaly in K 
# T0nh,T0sh = ocean temperature anomaly in K
# gnh,gsh = applied hemispheric SRM forcing in Wm-2
# f = global GHG forcing in Wm-2 
# geff = efficacy of SRM forcing 
# lam = lambda = feedback parameter Wm-2K-1
# gamma = heat exchange coefficient in Wm-2K-1
# tau_nh_sh_upper = timescale (yrs) of interhemispheric heat transfer for upper ocean layer
# tau_nh_sh_lower = timescale (yrs) of interhemispheric heat transfer for deep ocean layer
# C = atmosphere/land/upper-ocean heat capacity 
# C0 = deep-ocean heat capacity in W.yr.m-2.K-1
# ndt = number of timesteps in 1 yr
# dt = timestep in yr
# noise = noise in T - needs to put a more realistic climate noise
# also noise is only on Tf, should we put noise on T0f as well ?
#
  #--test sign geff 
  if geff<0:
      sys.exit('SRM efficacy geff has to be a positive number')
  #--discretize yearly timestep
  dt = 1./float(ndt)
  #--initial T and TO
  Ti_sh = Tsh ; T0i_sh = T0sh
  Ti_nh = Tnh ; T0i_nh = T0nh
  # time loop
  for i in range(ndt):
     #--sh
     Tf_sh  = Ti_sh + dt/C*(f+geff*gsh-lam*Ti_sh-gamma*(Ti_sh-T0i_sh))
     T0f_sh = T0i_sh + dt/C0*gamma*(Ti_sh-T0i_sh)
     #--nh
     Tf_nh  = Ti_nh + dt/C*(f+geff*gnh-lam*Ti_nh-gamma*(Ti_nh-T0i_nh))
     T0f_nh = T0i_nh + dt/C0*gamma*(Ti_nh-T0i_nh)
     #--reducing inter-hemispheric T gradient
     dT  = Tf_nh - Tf_sh
     dT0 = T0f_nh - T0f_sh
     Tf_sh = Tf_sh + dt/tau_nh_sh_upper * dT
     Tf_nh = Tf_nh - dt/tau_nh_sh_upper * dT
     T0f_sh = T0f_sh + dt/tau_nh_sh_lower * dT0
     T0f_nh = T0f_nh - dt/tau_nh_sh_lower * dT0
     #--preparing for next time substep
     Ti_sh  = Tf_sh 
     T0i_sh = T0f_sh
     Ti_nh  = Tf_nh 
     T0i_nh = T0f_nh
  # add noise on final Tf
  Tf_sh = Tf_sh + Tsh_noise
  Tf_nh = Tf_nh + Tnh_noise
  # GMST 
  Tf = (Tf_sh+Tf_nh)/2.
  #--return outputs
  return Tf, Tf_sh, Tf_nh, T0f_sh, T0f_nh
#
#---------------------------------------
#--simple climate NH/SH model from RF v2
#---------------------------------------
def clim_sh_nh_from_rf_v2(Tsh,Tnh,T0sh,T0nh,gsh,gnh,\
               f=1.,geff=1.,tau_nh_sh_upper=20.,tau_nh_sh_lower=20., \
               Csh=7.,Cnh=7,C0=100.,lambdash=1.,lambdanh=1.,gamma=0.7, ndt=10, Tnh_noise=0, Tsh_noise=0):
# simple climate model from Eq 1 and 2 in Geoffroy et al 
# https://journals.ametsoc.org/doi/pdf/10.1175/JCLI-D-12-00195.1
# Tnh,Tsh = surface air temperature anomaly in K 
# T0nh,T0sh = ocean temperature anomaly in K
# gnh,gsh = applied hemispheric SRM forcing in Wm-2
# f = global GHG forcing in Wm-2 
# geff = efficacy of SRM forcing 
# lambda nh/sh = feedback parameter Wm-2K-1
# gamma = heat exchange coefficient between the two layers in Wm-2K-1
# tau_nh_sh_upper = timescale (yrs) of interhemispheric heat transfer for upper ocean layer
# tau_nh_sh_lower = timescale (yrs) of interhemispheric heat transfer for deep ocean layer
# Csh / Cnh = hemispheric atmosphere/land/upper-ocean heat capacity 
# C0 = deep-ocean heat capacity in W.yr.m-2.K-1
# ndt = number of timesteps in 1 yr
# dt = timestep in yr
# noise = noise in T - needs to put a more realistic climate noise
# also noise is only on Tf, should we put noise on T0f as well ?
#
  #--test sign geff 
  if geff<0:
      sys.exit('SRM efficacy geff has to be a positive number')
  #--discretize yearly timestep
  dt = 1./float(ndt)
  #--initial T and TO
  Ti_sh = Tsh ; T0i_sh = T0sh
  Ti_nh = Tnh ; T0i_nh = T0nh
  # time loop
  for i in range(ndt):
     #--sh
     Tf_sh  = Ti_sh + dt/Csh*(f+geff*gsh-lambdash*Ti_sh-gamma*(Ti_sh-T0i_sh))
     T0f_sh = T0i_sh + dt/C0*gamma*(Ti_sh-T0i_sh)
     #--nh
     Tf_nh  = Ti_nh + dt/Cnh*(f+geff*gnh-lambdanh*Ti_nh-gamma*(Ti_nh-T0i_nh))
     T0f_nh = T0i_nh + dt/C0*gamma*(Ti_nh-T0i_nh)
     #--reducing inter-hemispheric T gradient
     dT  = Tf_nh - Tf_sh
     dT0 = T0f_nh - T0f_sh
     Tf_sh = Tf_sh + dt/tau_nh_sh_upper * dT
     Tf_nh = Tf_nh - dt/tau_nh_sh_upper * dT
     T0f_sh = T0f_sh + dt/tau_nh_sh_lower * dT0
     T0f_nh = T0f_nh - dt/tau_nh_sh_lower * dT0
     #--preparing for next time substep
     Ti_sh  = Tf_sh 
     T0i_sh = T0f_sh
     Ti_nh  = Tf_nh 
     T0i_nh = T0f_nh
  # add noise on final Tf
  Tf_sh = Tf_sh + Tsh_noise
  Tf_nh = Tf_nh + Tnh_noise
  # GMST 
  Tf = (Tf_sh+Tf_nh)/2.
  #--return outputs
  return Tf, Tf_sh, Tf_nh, T0f_sh, T0f_nh
