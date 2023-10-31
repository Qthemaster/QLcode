import pickle
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Define Gaussian function for fitting
def gaussian(x, amp, cen, wid):
    """ Gaussian function for fitting. """
    return amp * np.exp(-(x-cen)**2 / (2*wid**2))

# Define Lorentzian function for fitting
def lorentzian(x, amp, cen, wid):
    """ Lorentzian function for fitting. """
    return amp / (1 + ((x - cen)/wid)**2)

# Combined multiple peak fitting function with background
def multi_peak_with_background(x, *params):
    """ Combined Gaussian and Lorentzian function with background. """
    y = np.zeros_like(x) + params[-1]  # Background term
    idx = 0  # Initialize parameter index
    for _ in range(num_gaussians):  # Loop over all Gaussians
        amp, cen, wid = params[idx:idx+3]
        y = y + gaussian(x, amp, cen, wid)
        idx += 3
    for _ in range(num_lorentzians):  # Loop over all Lorentzians
        amp, cen, wid = params[idx:idx+3]
        y = y + lorentzian(x, amp, cen, wid)
        idx += 3
    return y

# Extract data from pickle files
def extract_data_from_pkl(filename):
    """ Extract data from given pickle file. """
    with open(filename, 'rb') as file:
        data = pickle.load(file)
    x = list(data['Total PL data'].keys())
    y = list(data['Total PL data'].values())
    x, y = zip(*sorted(zip(x, y)))  # Sort data by x-values
    return np.array(x), np.array(y)

# Compute FWHM for the peaks
def compute_fwhm(cen, wid, peak_type):
    """ Compute Full Width at Half Maximum (FWHM). """
    c = 299792458  # Speed of light in nm/ns
    if peak_type == 'gaussian':
        fwhm_wavelength = 2.35482 * wid  # Gaussian FWHM
    elif peak_type == 'lorentzian':
        fwhm_wavelength = 2 * wid  # Lorentzian FWHM
    else:
        raise ValueError('Invalid peak type')
    fwhm_frequency = c / (cen**2) * fwhm_wavelength  # Conversion from nm to GHz
    return fwhm_frequency

# Main execution
if __name__ == "__main__":
    # Prompt user to input file names
    filenames = []
    while True:
        filename = input("Please enter the path to a pkl file (or type 'end' to finish): ")
        if filename.lower() == 'end':
            break
        else:
            filenames.append(filename)

    # Concatenate data from all input files
    all_x, all_y = np.array([]), np.array([])
    for file in filenames:
        x, y = extract_data_from_pkl(file)
        all_x = np.concatenate((all_x, x))
        all_y = np.concatenate((all_y, y))
    
    # 使用 argsort 获取排序索引
    sort_index = np.argsort(all_x)
    
    # 使用排序索引对 all_x 和 all_y 进行排序
    sorted_all_x = all_x[sort_index]
    sorted_all_y = all_y[sort_index]
    
    # 如果需要的话，您可以再次将 sorted_all_x 和 sorted_all_y 赋值给 all_x 和 all_y
    all_x = sorted_all_x
    all_y = sorted_all_y
    
    # Prompt user for number of Gaussians and Lorentzians to fit
    num_gaussians = int(input("Please enter the number of Gaussians to fit: "))
    num_lorentzians = int(input("Please enter the number of Lorentzians to fit: "))

    # Gather initial guesses for parameters from user
    initial_guess = []
    for i in range(num_gaussians):
        amp = float(input(f"Enter initial amplitude for Gaussian {i+1}: "))
        cen = float(input(f"Enter initial center for Gaussian {i+1}: "))
        wid = float(input(f"Enter initial width for Gaussian {i+1}: "))
        initial_guess.extend([amp, cen, wid])
    for i in range(num_lorentzians):
        amp = float(input(f"Enter initial amplitude for Lorentzian {i+1}: "))
        cen = float(input(f"Enter initial center for Lorentzian {i+1}: "))
        wid = float(input(f"Enter initial width for Lorentzian {i+1}: "))
        initial_guess.extend([amp, cen, wid])
    
    # Include background estimation
    bg_value = float(input("Enter initial estimate for background value: "))
    initial_guess.append(bg_value)

    # Get title from user
    plot_title = input("Please enter the title for the plot: ")

    # Fit the data with the model function
    params, pcov = curve_fit(multi_peak_with_background, all_x, all_y, p0=initial_guess)  # 修改这里以获取参数协方差矩阵
    
    # Plot the results
    plt.figure(figsize=(10, 6))
    plt.plot(all_x, all_y, 'b.', label='Data')  # Data points
    
    # Plot total fit and individual components
    plt.plot(all_x, multi_peak_with_background(all_x, *params), 'k-', label='Total Fit')  # Changed color to black
    
    colors = ['g', 'r', 'c', 'm', 'y', 'orange', 'pink', 'purple', 'violet', 'indigo']  # List of colors
    
    # Index for parameter array
    idx = 0
    # Plot each Gaussian with FWHM annotation
    for i in range(num_gaussians):
        color = colors[i % len(colors)]  # Cycle through colors list
        amp, cen, wid = params[idx:idx+3]
        errors = np.sqrt(np.diag(pcov[idx:idx+3, idx:idx+3]))  # Extract errors for current peak
        fwhm = compute_fwhm(cen, wid, 'gaussian')
        fwhm_error = (fwhm / wid) * errors[2]  # Error propagation for FWHM
        frequency_error = errors[1]  # Frequency error is directly derived from the wavelength error
        plt.plot(all_x, gaussian(all_x, amp, cen, wid), color + '--', 
                 label=f'Gaussian peak at {cen:.4f}±{frequency_error:.4f} nm, FWHM: {fwhm:.2f}±{fwhm_error:.2f} GHz')
        idx += 3
    
    # Plot each Lorentzian with FWHM annotation
    for i in range(num_lorentzians):
        color = colors[(i + num_gaussians) % len(colors)]  # Cycle through colors list
        amp, cen, wid = params[idx:idx+3]
        errors = np.sqrt(np.diag(pcov[idx:idx+3, idx:idx+3]))  # Extract errors for current peak
        fwhm = compute_fwhm(cen, wid, 'lorentzian')
        fwhm_error = (fwhm / wid) * errors[2]  # Error propagation for FWHM
        frequency_error = errors[1]  # Frequency error is directly derived from the wavelength error
        plt.plot(all_x, lorentzian(all_x, amp, cen, wid), color + '--',
                 label=f'Lorentzian peak at {cen:.4f}±{frequency_error:.4f} nm, FWHM: {fwhm:.2f}±{fwhm_error:.2f} GHz')
        idx += 3
       
    
    # Compute residual sum of squares (RSS)
    residuals = all_y - multi_peak_with_background(all_x, *params)
    rss = np.sum(residuals**2)
    normalized_rss = rss / (len(all_x) - len(params))  # Normalized by the degrees of freedom
    
    
    # Compute the normalized chi-square statistic
    sigma = np.std(all_y)  # standard deviation of observed values
    chi_square = np.sum((residuals / sigma)**2)  # chi-square statistic
    normalized_chi_square = chi_square / (len(all_x) - len(params))  # normalized by the degrees of freedom
    # Output results
    print(f"RSS: {rss:.4f}")
    print(f"Normalized RSS: {normalized_rss:.4f}")
    print(f"Normalized Chi-Square: {normalized_chi_square:.4f}")

    # Output FWHM and fitting error
    idx = 0  # Reset index for parameter array
    for i in range(num_gaussians + num_lorentzians):
        if i < num_gaussians:
            peak_type = 'Gaussian'
        else:
            peak_type = 'Lorentzian'
        amp, cen, wid = params[idx:idx+3]
        fwhm = compute_fwhm(cen, wid, peak_type.lower())
        # Compute standard error of the parameters from covariance matrix
        errors = np.sqrt(np.diag(pcov[idx:idx+3, idx:idx+3]))
        fwhm_error = (fwhm / wid) * errors[2]  # Error propagation for FWHM
        print(f"{peak_type} {i+1}: FWHM = {fwhm:.2f} GHz ± {fwhm_error:.2f} GHz")
        idx += 3
    
    # Finalize plot
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Intensity')
    plt.title(plot_title)  # Use user-input title
    legend = plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), 
                        fancybox=True, shadow=True, ncol=2, fontsize='small')  # Place legend below the plot, outside the figure
    plt.tight_layout()  # Adjusts the plot to ensure everything fits without overlapping
    plt.subplots_adjust(bottom=0.35)  # Adjust bottom margin to make room for legend
    plt.show()