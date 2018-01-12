# Import smorgasbord
from __future__ import print_function
import pdb
import sys
import os
import copy
import numpy as np
import scipy.interpolate
import emcee

# Define physical constants
c = 3E8
h = 6.64E-34
k = 1.38E-23





def Fit(gal_dict,
        bands_frame,
        beta_vary = True,
        beta = 2.0,
        components = 2,
        kappa_0 = 0.051,
        kappa_0_lambda = 500E-6,
        plot = True,
        covar_unc = None,
        priors = None,
        full_posterior = False,
        verbose = True):
        """
        Function that runs the ChrisFit dust SED fitting routine.

        Arguments:
            gal_dict:           A dictionary, containing entries called 'name', 'distance', and 'redshift', giving the
                                values for the target source in  question
            bands_frame:        A dataframe, with columns called 'band', 'flux', and 'error', providing the relevant
                                values for each band for the target source in question

        Keyword arguments:
            beta_vary:          A boolean, stating whether or not beta (the emissivity slope) should a free parameter,
                                or fixed
            beta:               A float, or list of floats, stating the value(s) of beta to use. If only a single float
                                is given, this is used for all components. If beta_vary is set to true, beta will
                                provide starting position for MCMC
            components:         An integer, stating how many modified blackbody components should make up the model
                                being fit
            kappa_0:            The value of the dust mass absorption coefficient, kappa_d, to use to caculate dust mass
                                (uses Clark et al., 2016, value by default)
            kappa_0_lambda:     The reference wavelength for kappa_0; corresponding value of kappa_0 at other
                                wavelengths extrapolated via (kappa_0_lambda/lambda)**beta
            plot:               A boolean, stating whether to generate plots of the resulting SED fit
            covar_unc:          A list, each element of which (if any) is a dictionary describing band-covariant
                                uncertainties; for the 5% Hershcel-SPIRE band covariance, covar_unc would be:
                                [{'covar_bands':['SPIRE_250','SPIRE_350','SPIRE_500'],
                                'covar_scale':0.04,
                                'covar_distr':'flat'}],
                                where 'bands' describes the bands (as named in bands_frame) in question, 'covar_scale'
                                describes the size of the covariant component of the flux uncertainty (as a fraction of
                                measured source flux), and 'covar_dist' is the distribution of the uncertainty
                                (currently accepting either 'flat' or 'normal')
            priors:             A dictionary, of lists, of functions (yeah, I know); dictionary entries can be called
                                'temp', 'mass', and 'beta', each entry being an n-length list, where n is the number of
                                components, with the n-th list element being a function giving the prior for the
                                parameter in question (ie, temperature, mass, or beta) of the n-th model component
            full_posterior:     A boolean, stating whether the full posterior distribution of each paramter should be
                                returned, or just the summary of median, credible interval, etc
            verbose:            A boolean, stating whether ChrisFit should provide verbose output whilst operating
            """


        def LnLike(params, bands_frame, gal_dict, fit_dict):
            """ Funtion to compute ln-likelihood of some data, given the parameters of the proposed model """

            # Programatically dust temperature, dust mass, and beta (varible or fixed) parameter sub-vectors from params tuple
            temp_vector, mass_vector, beta_vector, covar_vector = ParamsExtract(params, fit_dict)

            # Loop over fluxes, to calculate the ln-likelihood of each, given the proposed model
            ln_like = -1.0
            for b in bands_frame.index.values:

                # Calculate predicted flux, given SED parameters                
                band_flux_pred = ModelFlux(bands_frame.loc[b,'wavelength'], temp_vector, mass_vector, gal_dict['distance'], kappa_0=kappa_0, kappa_0_lambda=kappa_0_lambda, beta=beta_vector)
                
                # Factor in colour corrections              
                col_correct_factor = ColourCorrect(band_flux_pred, bands_frame.loc[b], temp_vector, mass_vector, kappa_0, kappa_0_lambda, beta, verbose=verbose)
                band_flux_pred *= col_correct_factor[0]      
                
                # Factor in correlated uncertainties
                pdb.set_trace()
                
                # Calculate ln-likelihood of flux, given measurement uncertainties and proposed model
                ln_like *= ln_like
                
                
                
                
                # Factor in limits
                
                
                
                


            ### REMEMBER TO HANDLE LIMITS - JUST MAKE IT SO THAT LN-LIKELIHOODS BENEATH MOST-LIKELY VALUE ARE ALL SAME AS THE MOST LIKELY VALUE ###

            # Return data ln-likelihood
            return



        def LnPrior(params, fit_dict):
            """ Function to compute prior ln-likelihood of the parameters of the proposed model """

            # Programatically extract dust temperature, dust mass, and beta (varible or fixed) parameter sub-vectors from params tuple
            temp_vector, mass_vector, beta_vector, covar_vector = ParamsExtract(params, fit_dict)

            # Return prior ln-likelihood
            return



        def LnPost(params, bands_frame, fit_dict):
            """ Funtion to compute posterior ln-likelihood of the parameters of the proposed model, given some data """

            # Caculate prior ln-likelihood of the proposed model parameters
            ln_prior = LnPrior(params, fit_dict)

            # Caculate the ln-likelihood of the data, given the proposed model parameters
            ln_like = LnLike(params, bands_frame, fit_dict)

            # Calculate and return the posterior ln-likelihood of the proposed model parameters, given the data
            ln_post = ln_prior + ln_like
            return ln_post



        # Parse beta argument, so that each model component is assigned its own value (even if they are all the same)
        if not hasattr(beta, '__iter__'):
            beta = np.array([beta])
        if len(beta) == 1 and components > 1:
            beta = np.array([beta[0]] * int(components))
        elif len(beta) != int(components):
            Exception('Either provide a single value of beta, or a list of values of length the number of components')

        # Bundle various fitting argumnts in to a dictionary
        fit_dict = {'components':components,
                    'beta_vary':beta_vary,
                    'beta':beta,
                    'covar_unc':covar_unc}

        # Determine number of parameters
        n_params = (2 * int(components)) + int(fit_dict['beta_vary'])

        # Arbitrary test model        
        params = {'temp_1':21.73,'temp_2':21.73,
                  'mass_1':3.92*(10**7.93),'mass_2':3.92*(10**4.72),
                  'beta_1':2.0,'beta_2':2.0,
                  'covar_err_1':1.0}
        test = LnLike(params, bands_frame, gal_dict, fit_dict)
        pdb.set_trace()

        # Initiate emcee affine-invariant ensemble sampler       
        sampler = emcee.EnsembleSampler(n_walkers, n_params, LnPost, args=(bands_frame, fit_dict))










def ModelFlux(wavelength, temp, mass, dist, kappa_0=0.051, kappa_0_lambda=500E-6, beta=2.0, covar=None):
    """
    Function to caculate flux at given wavelength(s) from dust component(s) of given mass and temperature, at a given
    distance, assuming modified blackbody ('greybody') emission.

    Arguments:
        wavelength:     A float, or list of floats, giving the wavelength(s) (in m) of interest
        temp:           A float, or list of floats, giving the temperature(s) (in K) of each dust component
        mass:           A float, or list of floats, giving the mass(es) (in M_sol) of each dust component
        dist:           A float, giving the distance to the target source (in pc)

    Keyword arguments:
        kappa_0:        A float, or list of floats, giving the dust mass absorption coefficient(s) (in m**2 kg**-1),
                        kappa, of each dust component; reference wavelengths given by kwarg kappa_0_lambda
        kappa_0_lambda: A float, or list of floats, giving the reference wavelength (in m) coresponding to each value
                        of kappa_0
        beta:           A float, or list of floats, giving the dust emissivity slope(s), beta, of each dust component

    If wavelenghth is given as a list, a list of output fluxes will be given, corresponding to the calculated flux at
    each wavelength.

    Temperature and mass can be set to be lists , corresponding to multiple dust components. For n components, both
    lists must be of length n.

    Optionally, a different dust mass absorption coefficient (ie, kappa) can be used for each component; this is done by
    giving lists of length n for kappa_0 and kappa_0_lambda.

    Optionally, a different dust emissivity slope (ie, beta) can be used for each component; this is done by giving a
    list of length n for beta.
    """


    # Establish the number of model components
    if hasattr(temp, '__iter__') and hasattr(mass, '__iter__'):
        if len(temp) != len(mass):
            Exception('Number of dust components needs to be identical for temp and mass variables')
        else:
            n_comp = len(temp)
    elif not hasattr(temp, '__iter__') and not hasattr(mass, '__iter__'):
        n_comp = 1
    else:
        Exception('Number of dust components needs to be identical for temp and mass variables')
        
        

    # As needed, convert variables to arrays
    wavelength = Numpify(wavelength)
    temp = Numpify(temp)
    mass = Numpify(mass, n_target=n_comp)
    kappa_0 = Numpify(kappa_0, n_target=n_comp)
    kappa_0_lambda = Numpify(kappa_0_lambda, n_target=n_comp)
    beta = Numpify(beta, n_target=n_comp)

    # Check that variables are the same length, when they need to be
    if np.std([len(temp), len(mass), len(beta), len(kappa_0), len(kappa_0_lambda)]) != 0:
        Exception('Number of dust components needs to be identical for temp/mass/beta/kappa_0/kappa_0_lambda variables')

    """ NB: Arrays have dimensons of n_comp rows by n_bands columns """

    # Convert wavelengths to frequencies (for bands of interest, and for kappa_0 reference wavelengths)
    nu = np.divide(c, wavelength)
    nu_0 = np.divide(c, kappa_0_lambda)

    # Calculate kappa for the frequency of each band of interest
    kappa_nu_base = np.outer(nu_0**-1, nu) # This being the array-wise equivalent of nu/nu_0
    kappa_nu_prefactor = np.array([ np.power(kappa_nu_base[m,:],beta[m]) for m in range(n_comp) ]) # This expontiates each model component's base term to its corresponding beta
    kappa_nu = np.array([ np.multiply(kappa_0[m],kappa_nu_prefactor[m,:]) for m in range(n_comp) ])

    # Caclulate Planck function prefactor for each frequency
    B_prefactor = np.divide((2.0 * h * nu**3.0), c**2.0)

    # Calculate exponent term in Planck function, for each component, at each frequency
    B_exponent = np.array([ np.divide((h*nu),(k*temp[m])) for m in range(n_comp) ])

    # Calculate final value of Planck function for each, for each model component, at each frequency (output array will have n_comp rows, and n_freq columns)
    B_planck = B_prefactor * (np.e**B_exponent - 1)**-1.0

    # Convert mass and distance values to SI unuts
    mass_kilograms = mass * 2E30
    dist_metres = dist * 3.26 * 9.5E15

    # Calculate flux for each component, for each dust model component
    flux = 0.0
    for m in range(n_comp):
        flux += 1E26 * kappa_nu[m,:] * dist_metres**-2.0 * mass_kilograms[m] * B_planck[m,:]

    # Return calculated flux (denumpifying it if is only single value)
    if flux.size == 0:
        flux = flux[0]
    #flux([250E-6,350E-6,500E-6], [21.7,64.1], [3.92*(10**7.93),3.92*(10**4.72)], 25E6, kappa_0=[0.051,0.051], kappa_0_lambda=[500E-6,500E-6], beta=[2.0,2.0])
    return flux





def Numpify(var, n_target=False):
    """ Function for checking if variable is a list, and (if necessary) converting to a n_target length list of identical entries """

    # If variable is not iterable (ie, a list/array/etc), convert into an appropriate-length list
    if not hasattr(var, '__iter__'):
        if not n_target:
            var = [var]
        else:
            var = [var]*n_target

    # If necessary Convert a single-element iterable into a list of length n_targets
    elif len(var) == 1 and n_target > 1:
        var = [var[0]]*n_target

    # Object to mis-matched list lengths
    elif len(var) > 1 and len(var) != n_target:
        Exception('Variable list must either be of length 1, or of length n_targets')

    # If variable is not a numpy array, turn it into one
    if not isinstance(var, np.ndarray):
        var = np.array(var)

    # Return freshly-numpified variable
    return var



def ParamsExtract(params, fit_dict):
    """ Function to extract SED parameters from params dictionary. Resulting parameter tuple is structured:
    (temp_1, temp_2, ..., temp_n, 
    mass_1, mass_2, ..., mass_n, 
    beta_1, beta_2, ..., beta_n, 
    covar_err_1, covar_err_2, ..., covar_err_n)
    Note that beta values are only required input if fit_dict['beta_vary'] == True. """
    
    # Initiate parameter sub-vectors
    temp_vector = []
    mass_vector = []
    beta_vector = []
    covar_err_vector = []
    
    # Loop over keys of params dictionary, placing temperature, mass, and beta parameters into appropriate sub-vectors
    for param_key in sorted(params.keys()):
        if 'temp_' in param_key:
            temp_vector.append(params[param_key])
        elif 'mass_' in param_key:
            mass_vector.append(params[param_key])
        elif 'beta_' in param_key:
            beta_vector.append(params[param_key])
        elif 'covar_' in param_key:
            covar_err_vector.append(params[param_key])
        else:
            Exception('Key of entry in parameter dictionary does not match any expected parameter')

    # If beta isn't variable, just set beta using value from fit_dict
    if not fit_dict['beta_vary']:
        beta_vector = copy.deepcopy(fit_dict['beta']) 

    # Return parameters tuple
    return (tuple(temp_vector), tuple(mass_vector), tuple(beta_vector), tuple(covar_err_vector))
    
    
    
def ColourCorrect(band_flux_pred, band_frame, temp, mass, kappa_0, kappa_0_lambda, beta, verbose):
    """ Function to calculate colour-correction FACTOR appropriate to a given underlying spectrum. Will work for any
    instrument for which file 'Color_Corrections_INSTRUMENTNAME.csv' is found in the same directory as this script. """

    # Set location of ChrisFuncs.py to be current working directory, recording the old CWD toswitch back to later
    old_cwd = os.getcwd()
    os.chdir(str(os.path.dirname(os.path.realpath(sys.argv[0]))))

    # Identify instrument and wavelength, and read in corresponding colour-correction data
    unknown = False
    instrument = band_frame['band'].split('_')[0]
    try:
        try:
            data_table = np.genfromtxt('Colour_Corrections_'+instrument+'.csv', delimiter=',', names=True)
        except:
            data_table = np.genfromtxt(os.path.join('ChrisFit','Colour_Corrections_'+instrument+'.csv'), delimiter=',', names=True)
        data_index = data_table['alpha']
        data_column = 'K'+str(int((band_frame['wavelength']*1E6)))
        data_factor = data_table[data_column]
    except:
        unknown = True
        if verbose==False:
            print(' ')
            print('Instrument \''+instrument+'\' not recognised, no colour correction applied.')

    # If instrument successfuly identified, perform colour correction; otherwise, cease
    if unknown==True:
        factor = 1.0
        index = np.NaN
    elif unknown==False:

        # Calculate relative flux at wavelengths at points at wavelengths 1% to either side of target wavelength (no need for distance or kappa, as absolute value is irrelevant)
        lambda_plus = band_frame['wavelength']*1.01
        lambda_minus = band_frame['wavelength']*0.99
        flux_plus = ModelFlux(lambda_plus, temp, mass, 1E6, kappa_0=kappa_0, kappa_0_lambda=kappa_0_lambda, beta=beta)
        flux_minus = ModelFlux(lambda_minus, temp, mass, 1E6, kappa_0=kappa_0, kappa_0_lambda=kappa_0_lambda, beta=beta)

        # Determine spectral index
        index = -1.0 * ( np.log10(flux_plus) - np.log10(flux_minus) ) / ( np.log10(lambda_plus) - np.log10(lambda_minus) )

        # Use cubic spline interpolation to estimate colour-correction divisor at calculated spectral index
        interp = scipy.interpolate.interp1d(data_index, data_factor, kind='linear', bounds_error=None, fill_value='extrapolate')
        factor = interp(index)

    # Restore old cwd, and return results
    os.chdir(old_cwd)
    return factor, index


