"""Solve standard RBA problem."""

# python 2/3 compatibility
from __future__ import division, print_function

# package imports
import rba
import numpy as np


def main():
    
    # set input and putput paths
    # 'model/' or '../Bacillus-subtilis-168-WT/' or '../Escherichia-coli-K12-WT'
    xml_dir = 'model/'
    output_dir = 'simulation/'
    
    # load model, build matrices
    model = rba.RbaModel.from_xml(xml_dir)
    
    # optionally modify medium
    c_fruc = [10**i for i in np.arange(-4, 0.25, 0.25)]
    new_medium = model.medium
    
    # loop through a set of conditions
    for conc in c_fruc:
        new_medium['M_fru'] = conc
        model.medium = new_medium
        
        # solve model
        results = model.solve()
        
        # report results, for yield calculation supply transport
        # reaction and MW of substrate
        report_results(results,
            output_dir = output_dir,
            output_suffix = '_fru_' + str(conc) + '.tsv',
            substrate ='R_FRUpts2',  
            substrate_MW = 0.18
            )


def report_results(
    rba_result, output_dir, output_suffix,
    substrate = None, substrate_MW = None):
    
    # calculate yield
    # flux in mmol g_bm^-1 h^-1 needs to be converted to g substrate;
    # for fructose: MW = 180.16 g/mol = 0.18 g/mmol
    if substrate:
        yield_subs = rba_result.mu_opt / (rba_result.reaction_fluxes()[substrate] * substrate_MW)
    
    # export summary fluxes per reaction
    rba_result.write_fluxes(
        output_dir + 'fluxes' + output_suffix,
        file_type = 'tsv',
        merge_isozyme_reactions = True,
        only_nonzero = True,
        remove_prefix = True)
    
    # export enzyme concentrations
    rba_result.write_proteins(
        output_dir + 'proteins' + output_suffix,
        file_type = 'csv')
    
    # export growth rate, yield, and process machinery concentrations
    ma = rba_result.process_machinery_concentrations()
    ma['mu'] = rba_result.mu_opt
    if substrate:
        ma['yield'] = yield_subs
    with open(output_dir + 'macroprocesses' + output_suffix, 'w') as fout:
        fout.write('\n'.join(['{}\t{}'.format(k, v) for k, v in ma.items()]))
    
    # print µ_max and yield to terminal
    print('\n----- SUMMARY -----')
    print('\nOptimal growth rate is {}.'.format(rba_result.mu_opt))
    print('Yield on substrate is {}.'.format(yield_subs))
    # print top exchange fluxes
    rba_result.print_main_transport_reactions()


if __name__ == '__main__':
    main()
