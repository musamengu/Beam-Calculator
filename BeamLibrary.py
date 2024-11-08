import os
import __main__
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp
from image_manipulate import * #Custom Library
from setting import * #Custom Library


"""
# About Beam library:
A beam is a structural element that primarily resists loads applied laterally to the beam's axis.
Its mode of deflection is primarily by bending.

This library has several class and their methods in order to solve a 2d Beam numerically and do beam analysis.

## Sign Conventions:
Positive x-axis for beam: increases in right hand side
Positive y-axis for beam: increases upward direction
Positive angle direction: Counter clockwise with respect to beam positive x-axis
Positive moment: Counter clockwise

## Units Conventions:
Length: meter
Angle: degrees
Load: kN
Moment: kNm
"""


class Beam:
    """
        `Beam` is the main class to represent a beam object and perform various calculations.

        ## Attributes
        `length(float)`: length of a beam

        `kwargs`: Here are few optional keyword arguments
        - `E(float)` = Modulus of Elasticity of beam material 
        - `I(float)` = 2nd moment of area of the cross section of beam

        #### Example
        ```
        # to create a beam of length 5m:
        b = Beam(5)
        ```
    """
    # initial kwargs lists for simply supported beam
    simply_supported = ('Elasticity', 'MOA')

    def __init__(self, length: float, ndivs=500, **kwargs):
        
        self.double_integrel = [0,0]
        self.length = length

        #ndivs ayarlama, bunun sayesinde büyük kiriş uzunluklarında kasmadan sonuç açılabiliyor.
        if self.length>0 and self.length<=10:
            self.ndivs = 750
        if self.length>10 and self.length<=100:
            self.ndivs = 500
        if self.length>100 and self.length<=1000:
            self.ndivs = 350
        if self.length>1000 :
            self.ndivs = 250

          # this is required to create that number of points along which moment and shear values will be calculated
        # creating beam fragments of that beam points
        self.xbeam, self.dxbeam = np.linspace(0,
                                              self.length, self.ndivs, retstep=True)
        # cause we've initialized beam length from -1, we must keep track of where positive value for beam starts
        self.beam_0 = np.argwhere(self.xbeam >= 0)[0][0]

        # modulus of elasticity of the material
        self.E = kwargs.get('E') or kwargs.get('Elasticity')
        self.I = kwargs.get('I') or kwargs.get('MOA')  # second moment of area

        self.supports = kwargs.get('supports')
        # self.reactions
        # variables initialization for beam:
        self.x, self.V_x, self.M_x = sp.symbols('x V_x M_x')

        # intitial fx,fy,moment equations
        self.fx = 0  # sp.symbols('fx') #total sum of horizontal force
        self.fy = 0  # sp.symbols('fy') #total sum of vertical force
        # sp.symbols('m') #total sum of moments about any point on beam
        self.m = 0
        # total sum of moments about hinge (of one side of beam only)
        self.m_hinge = 0

        # initialize variable to store solved reactions, and macaulay's moment and shear function
        # initialize variable to store all support reactions in that beam
        self.reactions_list = []
        self.solved_rxns = None  # initialize variable to store solved values for reactions
        self.mom_fn = 0  # initialize variable to store bending moment values in numpy array
        self.shear_fn = 0  # initialize variable to store shear values in numpy array

        # this variables will hold numpy array of shear and moment values
        self.shear_values = None
        self.moment_values = None

        self.max_bm, self.posx_maxbm, self.min_bm, self.posx_minbm = 0.0, 0.0, 0.0, 0.0
        self.max_sf, self.posx_maxsf, self.min_sf, self.posx_minsf = 0.0, 0.0, 0.0, 0.0
        self.max_df, self.posx_maxdf, self.min_df, self.posx_mindf = 0.0, 0.0, 0.0, 0.0

    def add_loads(self, load_list: object):
        """
        ### Description:
        Adds different load values and Reaction variables to generate symbolic expression of all loads
        This will add respective component of different netload values. 
        `self.fx: x-components` and 
        `self.fy: y-components`

        #### Arguments
        `load_list` = List or Tuples of various load objects like `PointLoad, UDL, Reaction`

        """
        for loadtype in load_list:

            if isinstance(loadtype, PointLoad):   
                self.fx += loadtype.load_x
                self.fy += loadtype.load_y

            elif isinstance(loadtype, Reaction):
                if hasattr(loadtype, 'rx_var'):
                    self.fx += loadtype.rx_var
                    self.fy += loadtype.ry_var
                else:
                    self.fy += loadtype.ry_var

            elif isinstance(loadtype, UDL):
                self.fy += loadtype.netload  # adds net load value of udl object

            elif isinstance(loadtype, UVL):
                self.fy += loadtype.netload

    def add_moments(self, momgen_list: object, about: float = 0):
        """
        ### Description
        Receives a list or tuple of `PointLoad`, `Reaction`, `UDL` or `PointMoment` objects.
        Adds the moment due to those objects about origin.

        #### Sign Convention: 
        Anticlockwise moment are positively added. So, positive forces will give anticlockwise moments.

        #### Arguments and terms:
        - `momgen_list` = List or Tuples of various moment generators like `PointLoad, UDL, Reaction, PointMoment`
        - `about = 0`= Take moment about that x-coordinate in beam. `Default = 0, range = (0, self.length)`
        - `mom_gen(local variable)` = One which is capable of generating moment.
        """
        for mom_gen in momgen_list:  # takes moment about origin and adds up
            if isinstance(mom_gen, PointLoad):
                self.m += (mom_gen.pos-about)*mom_gen.load_y
            elif isinstance(mom_gen, UDL):
                self.m += (mom_gen.pos-about)*mom_gen.netload
            elif isinstance(mom_gen, UVL):
                self.m += (mom_gen.pos-about)*mom_gen.netload
            elif isinstance(mom_gen, Reaction):
                self.m += (mom_gen.pos-about)*mom_gen.ry_var
                if hasattr(mom_gen, 'mom_var'):
                    self.m += mom_gen.mom_var
            elif isinstance(mom_gen, PointMoment):
                self.m += mom_gen.mom

    def add_hinge(self, hinge : object, mom_gens : object):
        """
        ### Description:
        Internal hinges are provided in beam to make structure more flexible and able to resist external moments.
        It allows structure to move which reduces the reactive stresses. While, it's contribution in our program is
        that it will provide an extra equation for the beam.

        This function will modify `self.m_hinge` property of beam.
        Calling this funciton will calculate and add all moments hinge of all the loads to specified side (represented in `hinge.side`)

        ### Arguments:
        - `hinge` = object instance of `Hinge` class.
        - `mom_gens` = list of moment generators present on the beam.
        """
        if not isinstance(hinge, Hinge):
            raise ValueError(
                f"{hinge.__class__.__name__} object cannot be treated as Hinge object")

        # dictionary of loads separated to left and right of hinge
        separate_load = {
            'l': [mgen for mgen in mom_gens if mgen.pos < hinge.pos],
            # 'l' = moment generators to left of hinge
            'r': [mgen for mgen in mom_gens if mgen.pos > hinge.pos]
            # 'r' =  moment generators to right of hinge
        }

        # now take loads according to side specified in hinge class
        for side_mom_gen in separate_load[hinge.side[0]]:
            if isinstance(side_mom_gen, PointLoad):
                self.m_hinge += (side_mom_gen.pos -
                                 hinge.pos)*side_mom_gen.load_y
            elif isinstance(side_mom_gen, Reaction):
                self.m_hinge += (side_mom_gen.pos -
                                 hinge.pos)*side_mom_gen.ry_var
                if hasattr(side_mom_gen, 'mom_var'):
                    self.m_hinge += side_mom_gen.mom_var
            elif isinstance(side_mom_gen, PointMoment):
                self.m_hinge += side_mom_gen.mom
            elif isinstance(side_mom_gen, UDL):
                if side_mom_gen.end > hinge.pos & side_mom_gen.start < hinge.pos:
                    # cut and take left portion of udl
                    if hinge.side[0] == 'l':
                        cut_udl = UDL(
                            side_mom_gen.start, side_mom_gen.loadpm, hinge.pos-side_mom_gen.end)
                    else:
                        cut_udl = UDL(hinge.pos, side_mom_gen.loadpm,
                                      side_mom_gen.end-hinge.pos)

                    self.m_hinge += cut_udl.netload * \
                        (cut_udl.pos-hinge.pos)
                else:
                    self.m_hinge += side_mom_gen.netload * \
                        (side_mom_gen.pos-hinge.pos)

            elif isinstance(side_mom_gen, UVL):
                # to find the exact load/m value at position where hinge is:
                if side_mom_gen.start < hinge.pos & side_mom_gen.end > hinge.pos:
                    w_x = abs(side_mom_gen.startload +
                              side_mom_gen.gradient*(hinge.pos-side_mom_gen.start))
                    if hinge.side[0] == 'l':
                        cut_uvl = UVL(side_mom_gen.start, abs(
                            side_mom_gen.startload), hinge.pos-side_mom_gen.start, w_x)
                    else:
                        cut_uvl = UVL(hinge.pos, w_x, side_mom_gen.end -
                                      hinge.pos, abs(side_mom_gen.endload))

                    self.m_hinge += cut_uvl.netload * (cut_uvl.pos-hinge.pos)
                else:
                    self.m_hinge += side_mom_gen.netload * \
                        (side_mom_gen.pos-hinge.pos)

            elif isinstance(side_mom_gen, Reaction):
                self.m_hinge += (side_mom_gen.pos -
                                 hinge.pos)*side_mom_gen.ry_var
                if hasattr(side_mom_gen, 'mom_var'):
                    self.m_hinge += side_mom_gen.mom_var

    def calculate_reactions(self, reaction_list: object):
        """
        ### Description
        1. Generates 3 equations of static equilibrium: `self.fx=0 , self.fy=0,  self.m=0`.
        2. Uses `sympy.solve` to solve for symbolic variables `'rx_var', 'ry_var', 'mom_var'` in those equations. 
        3. Assign those values for unknown value of reactions object: `rx_val, ry_val, mom_val`.

        #### Arguments
        List or tuple of unknown reaction objects
        """
        Fx_eq = sp.Eq(self.fx, 0)
        Fy_eq = sp.Eq(self.fy, 0)
        M_eq = sp.Eq(self.m, 0)
        M_hinge = sp.Eq(self.m_hinge, 0)
        self.reactions_list = reaction_list


        eval_values = []  # initialize an empty list to contain reactions variables to be solved
        possible_rxn = ['rx_var', 'ry_var', 'mom_var']
        possible_values = ['rx_val', 'ry_val', 'mom_val']
        for rxn_obj in reaction_list:
            for rxn_var in possible_rxn:
                if hasattr(rxn_obj, rxn_var):
                    eval_values.append(getattr(rxn_obj, rxn_var))

        self.solved_rxns = sp.solve([Fx_eq, Fy_eq, M_eq, M_hinge], eval_values)
        # now assign values to the reaction objects too:
        for rxn_obj in reaction_list:
            for (rxn_val, rxn_var) in zip(possible_values, possible_rxn):
                if hasattr(rxn_obj, rxn_var):
                    setattr(rxn_obj, rxn_val,
                            float(self.solved_rxns[getattr(rxn_obj, rxn_var)]))

    def generate_shear_equation(self, loads):
        """
        ### Description
        1. Generates Macaulay's Equation for Shear Force due to various force generators
        2. Assigns symbolic expression of ShearForce to `self.shear_fn` attribute 
        3. Reassigns lambdified expression of ShearForce to `self.shear_fn`
        4. Reassigns `numpy.vectorize()` expression to `self.shear_fn`

        #### Arguments
        List or Tuple of various force generating objects:`PointLoad`, `Reaction`, `UDL` 
        """
        for force_gen in loads:
            if isinstance(force_gen, PointLoad):
                self.shear_fn += force_gen.load_y * \
                    sp.SingularityFunction('x', force_gen.pos, 0) 
            elif isinstance(force_gen, Reaction):
                self.shear_fn += force_gen.ry_val * \
                    sp.SingularityFunction('x', force_gen.pos, 0)
            elif isinstance(force_gen, UDL):
                self.shear_fn += force_gen.loadpm * \
                    sp.SingularityFunction('x', force_gen.start, 1)
                if force_gen.end < self.length:  # add udl in opposite direction
                    self.shear_fn -= force_gen.loadpm * \
                        sp.SingularityFunction('x', force_gen.end, 1)

            elif isinstance(force_gen, UVL):
                self.shear_fn += (force_gen.startload * sp.SingularityFunction('x', force_gen.start,
                                  1) + force_gen.gradient*sp.SingularityFunction('x', force_gen.start, 2)/2)
                if force_gen.end < self.length:  # add uvl in opposite direction
                    self.shear_fn -= (force_gen.endload * sp.SingularityFunction('x', force_gen.end,
                                      1) + force_gen.gradient*sp.SingularityFunction('x', force_gen.end, 2)/2)
            
        print("-----------shear equation-------------------")
        print(self.shear_fn)
        print("-----------shear equation----------------")

    def generate_moment_equation(self, loads: object):
        """
        ### Description
        1. Generates Macaulay's Equation for Moment due to various moment generators
        2. Assigns symbolic expression of BM to `self.mom_fn` attribute 
        3. Reassigns lambdified expression of BM to `self.mom_fn`
        4. Reassigns `numpy.vectorize()` expression to `self.mom_fn`

        #### Arguments
        List or Tuple of various moment generating objects:`PointLoad`, `Reaction`, `UDL` or `PointMoment`
        """
        for mom_gen in loads:
            if isinstance(mom_gen, PointLoad):
                self.mom_fn += mom_gen.load_y * \
                    sp.SingularityFunction('x', mom_gen.pos, 1)
            elif isinstance(mom_gen, Reaction):
                self.mom_fn +=( mom_gen.ry_val) * \
                    sp.SingularityFunction('x', mom_gen.pos, 1)
                if hasattr(mom_gen, 'mom_val'):
                    self.mom_fn -= (mom_gen.mom_val) * \
                        sp.SingularityFunction('x', mom_gen.pos, 0)
            elif isinstance(mom_gen, PointMoment):
                self.mom_fn -= mom_gen.mom * \
                    sp.SingularityFunction('x', mom_gen.pos, 0)
                # because we have defined anticlockwise moment positive in PointMoment
            elif isinstance(mom_gen, UDL):
                self.mom_fn += mom_gen.loadpm * \
                    sp.SingularityFunction('x', mom_gen.start, 2)/2
                if mom_gen.end < self.length:
                    self.mom_fn -= mom_gen.loadpm * \
                        sp.SingularityFunction('x', mom_gen.end, 2)/2

            elif isinstance(mom_gen, UVL):
                self.mom_fn += mom_gen.startload * sp.SingularityFunction(
                    'x', mom_gen.start, 2)/2 + mom_gen.gradient * sp.SingularityFunction('x', mom_gen.start, 3)/6
                if mom_gen.end < self.length:  # add uvl in opposite direction
                    self.mom_fn -= (mom_gen.endload * sp.SingularityFunction('x', mom_gen.end, 2) /
                                    2 + mom_gen.gradient * sp.SingularityFunction('x', mom_gen.end, 3)/6)
        print("-----------moment equation-------------------")
        print(self.mom_fn)
        print("-----------moment equation----------------")

    def generate_deflection_equation(self, loads: object):
        """
        ### Description
        1. Generates Macaulay's Equation for Moment due to various moment generators
        2. Assigns symbolic expression of BM to `self.mom_fn` attribute 
        3. Reassigns lambdified expression of BM to `self.mom_fn`
        4. Reassigns `numpy.vectorize()` expression to `self.mom_fn`

        #### Arguments
        List or Tuple of various moment generating objects:`PointLoad`, `Reaction`, `UDL` or `PointMoment`
        """

        reactionlar = []
        self.def_fn = 0
        x = sp.symbols('x')
        for def_gen in loads:

            if isinstance(def_gen, Reaction):######
                self.def_fn +=( def_gen.ry_val/6) * \
                    sp.SingularityFunction(x, def_gen.pos, 3)
                if hasattr(def_gen, 'mom_val'):
                    self.def_fn -= (def_gen.mom_val/2) * \
                        sp.SingularityFunction(x, def_gen.pos, 2)
                reactionlar.append(def_gen.pos)

            elif isinstance(def_gen, PointLoad):####

                self.def_fn += (def_gen.load_y/6) * \
                    sp.SingularityFunction(x, def_gen.pos, 3)
                    
            elif isinstance(def_gen, PointMoment):#####
                self.def_fn -= (def_gen.mom/2) * \
                    sp.SingularityFunction(x, def_gen.pos, 2)
                # because we have defined anticlockwise moment positive in PointMoment

            elif isinstance(def_gen, UDL):######
                self.def_fn += (def_gen.loadpm/12) * \
                    sp.SingularityFunction(x, def_gen.start, 4)/2
                if def_gen.end < self.length:
                    self.def_fn -= (def_gen.loadpm/12) * \
                        sp.SingularityFunction(x, def_gen.end, 4)/2

            elif isinstance(def_gen, UVL):
                self.def_fn += def_gen.startload * sp.SingularityFunction(
                    x, def_gen.start, 2)/2 + def_gen.gradient * sp.SingularityFunction(x, def_gen.start, 3)/6
                if def_gen.end < self.length:  # add uvl in opposite direction
                    self.def_fn -= (def_gen.endload * sp.SingularityFunction(x, def_gen.end, 2) /
                                    2 + def_gen.gradient * sp.SingularityFunction(x, def_gen.end, 3)/6)
        
        
        if len(reactionlar)>1:
            Equation_liste = []
            a,b = sp.symbols('a b')
            for reaction in reactionlar:

                sonuc = (self.def_fn.subs(x, reaction).evalf())
                Equation = sp.Eq(sonuc+a*reaction+b,0)
                Equation_liste.append(Equation)

        
            solution = sp.solve(Equation_liste,(a,b))
            self.double_integrel[0]=solution[a]
            self.double_integrel[1]=solution[b]

            if solution[a]<0:
                self.def_fn -= (sp.SingularityFunction(-1*(solution[a])*x,0,1))+solution[b]
            else:
                self.def_fn += (sp.SingularityFunction((solution[a])*x,0,1))+solution[b]

        #print("-----------deflection equation-------------------")
        #print(self.def_fn)
        #print("-----------deflection equation----------------")

    def generate_deflection_values(self, loads: object):
        """
        ### Description
        1. Generates Bending Moment Values due to various moment generators along several x positions on beam.
        2. Returns numpy 1d array of bending moment values

        #### Arguments
        - `loads` = List or Tuple of various moment generating objects:`PointLoad`, `Reaction`, `UDL` or `PointMoment`
        """
        self.deflection_values = np.zeros_like(self.xbeam)
        macaulay = np.vectorize(sp.SingularityFunction, otypes=[float])

        
        for load in loads:
            if isinstance(load, Reaction):
                if load.type== 'fixed' and load.pos==self.length:
                    self.sagdami = True
                else:
                    self.sagdami = False

        for mom_gen in loads:

            if isinstance(mom_gen, Reaction):

                if self.sagdami==True:
                    mom_gen.pos = self.length-mom_gen.pos

                    self.deflection_values +=( mom_gen.ry_val/6) * \
                        macaulay(self.xbeam, mom_gen.pos, 3)
                    if hasattr(mom_gen, 'mom_val'):
                        self.deflection_values += (mom_gen.mom_val/2) * \
                            macaulay(self.xbeam, mom_gen.pos, 2)

                else:

                    self.deflection_values +=( mom_gen.ry_val/6) * \
                        macaulay(self.xbeam, mom_gen.pos, 3)
                    if hasattr(mom_gen, 'mom_val'):
                        self.deflection_values -= (mom_gen.mom_val/2) * \
                            macaulay(self.xbeam, mom_gen.pos, 2)

            elif isinstance(mom_gen, PointLoad):

                if self.sagdami==True:
                    mom_gen.pos = self.length - mom_gen.pos

                self.deflection_values += (mom_gen.load_y/6) * \
                    macaulay(self.xbeam, mom_gen.pos, 3)
                    
            elif isinstance(mom_gen, PointMoment):

                if self.sagdami==True:
                    mom_gen.pos = self.length - mom_gen.pos

                self.deflection_values -= (mom_gen.mom/2) * \
                    macaulay(self.xbeam, mom_gen.pos, 2)
                
                # because we have defined anticlockwise moment positive in PointMoment
            elif isinstance(mom_gen, UDL):

                if self.sagdami==True:
                    mom_gen.end = self.length - mom_gen.end
                    mom_gen.start = self.length - mom_gen.start

                self.deflection_values += (mom_gen.loadpm/12) * \
                    macaulay(self.xbeam, mom_gen.start, 4)/2
                if mom_gen.end < self.length:
                    self.deflection_values -= (mom_gen.loadpm/12) * \
                        macaulay(self.xbeam, mom_gen.end, 4)/2

            elif isinstance(mom_gen, UVL):

                if self.sagdami==True:
                    mom_gen.start = self.length - mom_gen.end
                    mom_gen.end = self.length - mom_gen.start

                self.deflection_values += mom_gen.startload * \
                    macaulay(self.xbeam, mom_gen.start, 2)/2 + \
                    mom_gen.gradient * macaulay(self.xbeam, mom_gen.start, 3)/6
                if mom_gen.end < self.length:  # add uvl in opposite direction
                    self.deflection_values -= (mom_gen.endload * macaulay(self.xbeam, mom_gen.end, 2) /
                                           2 + mom_gen.gradient * macaulay(self.xbeam, mom_gen.end, 3)/6)

        E = (JsonEkle.bilgi_oku("Young's Module")/BirimiDegistir(JsonEkle.bilgi_oku("Force Unit"),"2").degistir())
        E = E*(BirimiDegistir(JsonEkle.bilgi_oku("Length Unit"),"2").degistir())**2
        I = JsonEkle.bilgi_oku("Moment Of Inertia")/(BirimiDegistir(JsonEkle.bilgi_oku("Length Unit"),"2").degistir())**4
        E_I = E*I


        self.deflection_values = self.deflection_values + self.xbeam*self.double_integrel[0]+self.double_integrel[1]

        
        self.deflection_values = (BirimiDegistir(JsonEkle.bilgi_oku("Length Unit"),"2").degistir())*(self.deflection_values/(E_I))

        if self.sagdami:
            self.deflection_values = self.deflection_values[::-1]

        return self.deflection_values

    def generate_shear_values(self, loads: object):
        """
        ### Description
        1. Generates Shear Force values due to various force generators along several x positions on beam.
        2. Returns numpy 1d array of those shear values

        #### Arguments
        - `loads` = List or Tuple of various force generating objects:`PointLoad`, `Reaction`, `UDL` 
        """

        self.shear_values = np.zeros_like(self.xbeam)
        macaulay = np.vectorize(sp.SingularityFunction, otypes=[float])

        for force_gen in loads:
            if isinstance(force_gen, PointLoad):
                self.shear_values += force_gen.load_y * \
                    macaulay(self.xbeam, force_gen.pos, 0)
            elif isinstance(force_gen, Reaction):
                self.shear_values += force_gen.ry_val * \
                    macaulay(self.xbeam, force_gen.pos, 0)

            elif isinstance(force_gen, UDL):
                self.shear_values += force_gen.loadpm * \
                    macaulay(self.xbeam, force_gen.start, 1)
                if force_gen.end < self.length:  # add udl in opposite direction
                    self.shear_values -= force_gen.loadpm * \
                        macaulay(self.xbeam, force_gen.end, 1)

            elif isinstance(force_gen, UVL):
                self.shear_values += (force_gen.startload * macaulay(self.xbeam, force_gen.start,
                                      1) + force_gen.gradient*macaulay(self.xbeam, force_gen.start, 2)/2)
                if force_gen.end < self.length:  # add uvl in opposite direction
                    self.shear_values -= (force_gen.endload * macaulay(self.xbeam, force_gen.end,
                                          1) + force_gen.gradient*macaulay(self.xbeam, force_gen.end, 2)/2)

        return self.shear_values

    def generate_moment_values(self, loads: object):
        """
        ### Description
        1. Generates Bending Moment Values due to various moment generators along several x positions on beam.
        2. Returns numpy 1d array of bending moment values

        #### Arguments
        - `loads` = List or Tuple of various moment generating objects:`PointLoad`, `Reaction`, `UDL` or `PointMoment`
        """
        self.moment_values = np.zeros_like(self.xbeam)
        macaulay = np.vectorize(sp.SingularityFunction, otypes=[float])


        for mom_gen in loads:
            if isinstance(mom_gen, PointLoad):
                self.moment_values += mom_gen.load_y * \
                    macaulay(self.xbeam, mom_gen.pos, 1)
            elif isinstance(mom_gen, Reaction):
                self.moment_values += mom_gen.ry_val * \
                    macaulay(self.xbeam, mom_gen.pos, 1)
                if hasattr(mom_gen, 'mom_val'):
                    self.moment_values -= mom_gen.mom_val * \
                        macaulay(self.xbeam, mom_gen.pos, 0)
            elif isinstance(mom_gen, PointMoment):
                self.moment_values -= mom_gen.mom * \
                    macaulay(self.xbeam, mom_gen.pos, 0)
                # because we have defined anticlockwise moment positive in PointMoment
            elif isinstance(mom_gen, UDL):
                self.moment_values += mom_gen.loadpm * \
                    macaulay(self.xbeam, mom_gen.start, 2)/2
                if mom_gen.end < self.length:
                    self.moment_values -= mom_gen.loadpm * \
                        macaulay(self.xbeam, mom_gen.end, 2)/2

            elif isinstance(mom_gen, UVL):
                self.moment_values += mom_gen.startload * \
                    macaulay(self.xbeam, mom_gen.start, 2)/2 + \
                    mom_gen.gradient * macaulay(self.xbeam, mom_gen.start, 3)/6
                if mom_gen.end < self.length:  # add uvl in opposite direction
                    self.moment_values -= (mom_gen.endload * macaulay(self.xbeam, mom_gen.end, 2) /
                                           2 + mom_gen.gradient * macaulay(self.xbeam, mom_gen.end, 3)/6)

        return self.moment_values

    def generate_significant_values(self):
        """
        # Description
        Generates significant values of shear force diagram like minimum and maximum bending moment, shear force etc.
        """
        self.max_bm, self.posx_maxbm, self.min_bm, self.posx_minbm = np.max(self.moment_values), self.xbeam[np.argmax(
            self.moment_values)], np.min(self.moment_values), self.xbeam[np.argmin(self.moment_values)]
        self.max_sf, self.posx_maxsf, self.min_sf, self.posx_minsf = np.max(self.shear_values), self.xbeam[np.argmax(
            self.shear_values)], np.min(self.shear_values), self.xbeam[np.argmin(self.shear_values)]

        self.max_df, self.posx_maxdf, self.min_df, self.posx_mindf = np.max(self.deflection_values), self.xbeam[np.argmax(
            self.deflection_values)], np.min(self.deflection_values), self.xbeam[np.argmin(self.deflection_values)]
        
        self.sig_value = [self.max_bm, self.min_bm, self.max_df, self.min_df, self.max_sf, self.min_sf]

        # Listede her bir değeri index ile güncelleyelim
        for i in range(len(self.sig_value)):
            if abs(self.sig_value[i]) >= 10:
                self.sig_value[i] = round(self.sig_value[i], 2)
            elif 0 < abs(self.sig_value[i]) < 10:
                self.sig_value[i] = round(self.sig_value[i], 3)
            elif abs(self.sig_value[i]) < 0:
                self.sig_value[i] = round(self.sig_value[i], 4)

        self.max_bm, self.min_bm, self.max_df, self.min_df, self.max_sf, self.min_sf = self.sig_value[0], self.sig_value[1],self.sig_value[2],self.sig_value[3],self.sig_value[4],self.sig_value[5]

    def fast_solve(self, loads_list: object, n: int = 1000):
        """
        ### Description
        This function will:
        1. solve for the unknown reactions
        2. generate shear function (can be accessed by `shear_fn`)
        3. generate moment function (can be accessed by `mom_fn`)
        4. generate shear force values (can be accessed by `shear_values`)
        5. generate bending moment values (can be accessed by `moment_values`)

        #### Arguments
        - `loads_list` = List (or tuple) of every possible beam objects like Reactions, Loads, Moments, Internal Hinge
        - `n:int = 1000` = Number of shear and moment values to create
        """
        hin = None
        rxns = [rxn for rxn in loads_list if isinstance(rxn, Reaction)]


        for obj in loads_list:
            if isinstance(obj, Hinge):
                hin = obj

        self.add_loads(load_list=loads_list)
        self.add_moments(loads_list)
        if hin:
            self.add_hinge(hin, loads_list)
        self.calculate_reactions(rxns)
        #self.generate_shear_equation(loads_list)
        self.generate_shear_values(loads_list)
        #self.generate_moment_equation(loads_list)
        self.generate_moment_values(loads_list)
        self.generate_deflection_equation(loads_list)
        self.generate_deflection_values(loads_list)
        
        #self.save_data(fname="C:/Users/mengu/OneDrive/Masaüstü/dosya",fformat="txt") #Verileri txt dosyası halinde kaydeder.

    def generate_graph_tek(self, which: str = 'both', save_fig: bool = False, filename: str = None, extension: str = 'png', res: str = 'low', show_graph: bool = True, **kwargs):
        """
        To generate bending moment diagram for beam with all reactions solved
        # Arguments:
        - `which:str ='both'` = To specify which graph to show. Default value = `'both'`
            - Accepted values `('bmd', 'sfd', 'both')`
        - `save_fig:bool` = To specify whether or not to save the generated image locally
        - `filename:str` = Name of file or file path to specify the location to save the generated image
        - `extension: str = 'png' ` = File extension to save the generate image. Supported extensions are ` ('png', 'pdf', 'eps', 'svg')`. By default `png`.
        - `details: bool` = To specify whether or not to show salient features in graph like contraflexure, inflexion
        - `res: str = 'low'` = Resolution of graph to be shown or saved.
        - `show_graph: bool = True` Whether or not to show the generate graph.
            - Note: Don't use res(values other than low) and `show_graph=True` together. It will create render error.
        """

        if self.length<=10 and self.length>0:
            self.artis = 1
        
        else:
            self.artis = int(self.length/10)

        # Rc parameters:
        plt.rc('font', family='serif', size=12)
        plt.rc('axes', autolimit_mode='round_numbers')

        diagrams = ('bmd', 'sfd','dd')
        if which.lower() in diagrams:
            pass
        else:
            raise ValueError(f"Unexpected graph type {which}")

        resolution = {'high': 500, 'medium': 250, 'low': 100,
                      'h': 500, 'm': 250, 'l': 100}  # list of possible resolutions
        if res.lower() in resolution.keys():
            DPI = resolution[res]
        else:
            raise ValueError(
                f"Unexpected resolution type {res}\n Use 'high' or 'medium' or 'low'")

        formats = ('png', 'pdf', 'eps', 'svg')
        if extension.lower() in formats:
            pass
        else:
            raise ValueError(
                f"Unknown image extension {extension}\n Supported extensions are: {formats}")

        # (y,x) in matplotib graph for maximum bending moment

        if which == 'bmd':
            fig, ax = plt.subplots(
                facecolor='w', edgecolor='w', num=TEXT_41, dpi=DPI)
            ax.plot(self.xbeam, self.moment_values,color='green', label=TEXT_43)
            ax.fill_between(self.xbeam, self.moment_values, where=(self.moment_values < 0), color='green', alpha=0.1)
            ax.fill_between(self.xbeam, self.moment_values, where=(self.moment_values >= 0), color='green', alpha=0.1)
            ax.set_xticks(range(0, int(self.length+1), self.artis))
            ax.set_xlim(0, self.length)
            ax.axhline(y=0, linewidth=3, color='k', label=TEXT_44)
            ax.set_title(TEXT_41)
            ax.set_xlabel(f"x {BirimiDegistir(JsonEkle.bilgi_oku("Length Unit"),"0").degistir()}")
            ax.set_ylabel(f"{TEXT_42} {JsonEkle.bilgi_oku("Moment Unit")}")
            ax.legend(fontsize=8)
            ax.grid(linewidth=1, color='gainsboro')

            if kwargs.get('details') == True:
                self.generate_significant_values()
                if round(self.max_bm, 0) != 0:
                    ax.plot(self.posx_maxbm, self.max_bm,
                            c='0.5', marker='o', ms=5)
                    ax.text(self.posx_maxbm, self.max_bm+50*self.max_bm/1000, s=r"$M_{max}$ = "+str(
                        round(self.max_bm, 1))+' ', fontsize=15, fontweight='light')

                # plotting 0 as min bending moment will interfere with beam line
                if round(self.min_bm, 0) != 0:
                    ax.plot(self.posx_minbm, self.min_bm,
                            c='0.5', marker='o', ms=5)
                    ax.text(self.posx_minbm+10*self.dxbeam, self.min_bm-50*self.max_bm/1000,
                            s=r"$M_{min}$ = "+str(round(self.min_bm, 1))+' ', fontsize=15, fontweight='light')

        if which == 'sfd':
            fig, ax = plt.subplots(
                facecolor='w', edgecolor='w', num=TEXT_45, dpi=DPI)
            ax.plot(self.xbeam, self.shear_values, color='orange', label=TEXT_47)
            ax.fill_between(self.xbeam, self.shear_values, where=(self.shear_values < 0), color='orange', alpha=0.1)
            ax.fill_between(self.xbeam, self.shear_values, where=(self.shear_values >= 0), color='orange', alpha=0.1)
            ax.set_xticks(range(0, int(self.length+1), self.artis))
            ax.set_xlim(0, self.length)
            ax.axhline(y=0, linewidth=3, color='k', label=TEXT_44)
            ax.set_title(TEXT_45)
            ax.set_xlabel(f"x {BirimiDegistir(JsonEkle.bilgi_oku("Length Unit"),"0").degistir()}")
            ax.set_ylabel(f"{TEXT_46} {BirimiDegistir(JsonEkle.bilgi_oku("Force Unit"),"0").degistir()}")
            ax.legend(fontsize=8)
            ax.grid(linewidth=1, color='gainsboro')

            if kwargs.get('details') == True:
                self.generate_significant_values()
                if round(self.max_sf, 0) != 0:
                    ax.plot(self.posx_maxsf, self.max_sf,
                            c='0.5', marker='o', ms=5)
                    ax.text(self.posx_maxsf+10*self.dxbeam, self.max_sf+50*self.max_sf/1000,
                            s=r"$V_{max}$ = "+str(round(self.max_sf, 1)), fontsize=15, fontweight='light')
                if round(self.min_sf, 0) != 0:
                    ax.plot(self.posx_minsf, self.min_sf,
                            c='0.5', marker='o', ms=5)
                    ax.text(self.posx_minsf+10*self.dxbeam, self.min_sf-50*self.max_sf/1000,
                            s=r"$V_{min}$ = "+str(round(self.min_sf, 1)), fontsize=15, fontweight='light')

        if which == 'dd':

            self.deflection_values = np.array([np.float64(float(val)) if isinstance(val, sp.Float) else val for val in self.deflection_values], dtype=np.float64)
            fig, ax = plt.subplots(facecolor='w', edgecolor='w', num=TEXT_48, dpi=DPI)
            ax.plot(self.xbeam, self.deflection_values,color='blue', label=TEXT_49)
            ax.fill_between(self.xbeam, self.deflection_values, where=(self.deflection_values < 0), color='blue', alpha=0.1)
            ax.fill_between(self.xbeam, self.deflection_values, where=(self.deflection_values >= 0), color='blue', alpha=0.1)
            ax.set_xticks(range(0, int(self.length+1), self.artis))
            ax.set_xlim(0, self.length)
            ax.axhline(y=0, linewidth=3, color='k', label=TEXT_44)
            ax.set_title(TEXT_48)
            ax.set_xlabel(f"x {BirimiDegistir(JsonEkle.bilgi_oku("Length Unit"),"0").degistir()}")
            ax.set_ylabel(f"{TEXT_49} (mm)")
            ax.legend(fontsize=8)
            ax.grid(linewidth=1, color='gainsboro')
            

            if kwargs.get('details') == True:
                self.generate_significant_values()

                if round(self.max_df, 0) != 0:
                    ax.plot(self.posx_maxdf, self.max_df,
                            c='0.5', marker='o', ms=5)
                    ax.text(self.posx_maxdf, self.max_df+50*self.max_df/1000, s=r"$Y_{max}$ = "+str(
                        round(self.max_df, 3)), fontsize=15, fontweight=15)

                # plotting 0 as min bending moment will interfere with beam line
                if round(self.min_df, 0) != 0:
                    ax.plot(self.posx_mindf, self.min_df,
                            c='0.5', marker='o', ms=5)
                    ax.text(self.posx_mindf+10*self.dxbeam, self.min_df-50*self.max_df/1000,
                            s=r"$Y_{min}$ = "+str(round(self.min_df, 3)), fontsize=15, fontweight='light')

        if save_fig:
            main_file_name = __main__.__file__.split('/')[-1]
            if filename == None:
                store_dir = __main__.__file__.replace(
                    main_file_name, 'images/')
                print(store_dir)
                try:
                    # try to create images/ directory in same directory level
                    os.mkdir(store_dir)
                except FileExistsError:
                    # now append full file name
                    filename = f"{store_dir}{__main__.__file__.split('/')[-1][:-3]}.png"
                    plt.savefig(filename)
                else:
                    filename = f"{store_dir}/{__main__.__file__.split('/')[-1][:-3]}.png"
                    plt.savefig(filename)
            else:
                if filename[-3:] in formats and '.' == filename[-4]:
                    save_path = __main__.__file__.replace(
                        main_file_name, filename)
                else:
                    save_path = __main__.__file__.replace(
                        main_file_name, f'{filename}.{extension}')
                plt.savefig(save_path, dpi=DPI)

        if show_graph:
            plt.show()

    def generate_graph_coklu(self, which: str = 'both', save_fig: bool = False, filename: str = None, extension: str = 'png', res: str = 'low', show_graph: bool = True, **kwargs):
        """
        To generate bending moment diagram for beam with all reactions solved
        # Arguments:
        - `which:str ='both'` = To specify which graph to show. Default value = `'both'`
            - Accepted values `('bmd', 'sfd', 'both')`
        - `save_fig:bool` = To specify whether or not to save the generated image locally
        - `filename:str` = Name of file or file path to specify the location to save the generated image
        - `extension: str = 'png' ` = File extension to save the generate image. Supported extensions are ` ('png', 'pdf', 'eps', 'svg')`. By default `png`.
        - `details: bool` = To specify whether or not to show salient features in graph like contraflexure, inflexion
        - `res: str = 'low'` = Resolution of graph to be shown or saved.
        - `show_graph: bool = True` Whether or not to show the generate graph.
            - Note: Don't use res(values other than low) and `show_graph=True` together. It will create render error.
        """
        if self.length<=10 and self.length>0:
            self.artis = 1
        else:
            self.artis = int(self.length/10)

        # Rc parameters:
        plt.rc('font', family='serif', size=12)
        plt.rc('axes', autolimit_mode='round_numbers')
        
        diagrams = ('bmd', 'sfd', 'both','def')
        

        resolution = {'high': 500, 'medium': 250, 'low': 100,
                      'h': 500, 'm': 250, 'l': 100}  # list of possible resolutions
        if res.lower() in resolution.keys():
            DPI = resolution[res]
        else:
            raise ValueError(
                f"Unexpected resolution type {res}\n Use 'high' or 'medium' or 'low'")

        formats = ('png', 'pdf', 'eps', 'svg')
        if extension.lower() in formats:
            pass
        else:
            raise ValueError(
                f"Unknown image extension {extension}\n Supported extensions are: {formats}")

        sirali_deger = ['sfd','bmd','dd'] #Diagramları Yukarıdan Aşağı Bu Sıraya Göre Gösterir.
        which = sorted(which, key=lambda x: sirali_deger.index(x))

        
        fig, axs = plt.subplots(nrows=len(which), ncols=1, figsize=(10, 10), edgecolor='w', facecolor='w', sharex=True, num=TEXT_51, dpi=DPI)
        
        for i,data in enumerate(which):
            self.generate_significant_values()
            if data == 'sfd':
                title = TEXT_45
                y_label = f"{TEXT_46} {BirimiDegistir(JsonEkle.bilgi_oku("Force Unit"),"0").degistir()}"
                value = self.shear_values
                renk = 'orange'
                max_bm = self.max_sf
                min_bm = self.min_sf
                posx_maxbm = self.posx_maxsf
                posx_minbm = self.posx_minsf
                x_max = r"$V_{max}$ = "
                x_min = r"$V_{min}$ = "
                which[i] = TEXT_47

            if data == 'dd':
                title = TEXT_48
                y_label = f"{TEXT_49} (mm)"
                value = self.deflection_values
                renk = 'blue'
                max_bm = self.max_df
                min_bm = self.min_df
                posx_maxbm = self.posx_maxdf
                posx_minbm = self.posx_mindf
                x_max = r"$Y_{max}$ = "
                x_min = r"$Y_{min}$ = "
                which[i] = TEXT_49
                
            if data == 'bmd':
                title = TEXT_41
                y_label = f"{TEXT_42} {JsonEkle.bilgi_oku("Moment Unit")}"
                value = self.moment_values
                renk = 'green'
                max_bm = self.max_bm
                min_bm = self.min_bm
                posx_maxbm = self.posx_maxbm
                posx_minbm = self.posx_minbm
                x_max = r"$M_{max}$ = "
                x_min = r"$M_{min}$ = "
                which[i] = TEXT_43

            value = np.array([np.float64(float(val)) if isinstance(val, sp.Float) else val for val in value], dtype=np.float64)

            axs[i].plot(self.xbeam, value, color=renk)
            axs[i].fill_between(self.xbeam, value, where=(value < 0), color=renk, alpha=0.1)
            axs[i].fill_between(self.xbeam, value, where=(value >= 0), color=renk, alpha=0.1)
            axs[i].set_xticks(range(0, int(self.length+1), self.artis))##########################################################################
            axs[i].set_title(title)
            axs[i].set_ylabel(y_label)

            if (len(which)-1)==i:
                axs[i].set_xlabel(f"x {BirimiDegistir(JsonEkle.bilgi_oku("Length Unit"),"0").degistir()}")

            if len(which)==3:
                fig.suptitle(f"{TEXT_50}")
            
            if len(which)==2:
                fig.suptitle(f"{which[0]} and {which[1]} Diagrams")

            for ax in axs:
                ax.set_xlim(0, self.length)
                ax.axhline(y=0, linewidth=3, color='k')
                ax.grid(linewidth=1, color='gainsboro')

            if kwargs.get('details') == True:
                if round(max_bm, 0) != 0:

                    axs[i].plot(posx_maxbm, max_bm,
                                c='0.5', marker='o', ms=5)
                    axs[i].text(posx_maxbm, max_bm+50*max_bm/1000, s=x_max+str(
                        round(max_bm, 1)), fontsize=15, fontweight='light')
                    
                if round(min_bm, 0) != 0:
                    axs[i].plot(posx_minbm, min_bm,
                                c='0.5', marker='o', ms=5)
                    axs[i].text(posx_minbm+10*self.dxbeam,min_bm-50*max_bm/1000,
                                s=x_min+str(round(min_bm, 2)), fontsize=15, fontweight='light')






        if save_fig:
            main_file_name = __main__.__file__.split('/')[-1]
            if filename == None:
                store_dir = __main__.__file__.replace(
                    main_file_name, 'images/')
                print(store_dir)
                try:
                    # try to create images/ directory in same directory level
                    os.mkdir(store_dir)
                except FileExistsError:
                    # now append full file name
                    filename = f"{store_dir}{__main__.__file__.split('/')[-1][:-3]}.png"
                    plt.savefig(filename)
                else:
                    filename = f"{store_dir}/{__main__.__file__.split('/')[-1][:-3]}.png"
                    plt.savefig(filename)
            else:
                if filename[-3:] in formats and '.' == filename[-4]:
                    save_path = __main__.__file__.replace(
                        main_file_name, filename)
                else:
                    save_path = __main__.__file__.replace(
                        main_file_name, f'{filename}.{extension}')
                plt.savefig(save_path, dpi=DPI)

        if show_graph:
            plt.show()

    def save_data(self, fname: str, fformat: str = 'txt'): #verileri txt halinde kaydeder.
        """
        ### Description
        Saves numerical values of Shear Forces and Moment Values in text file 
        The number of data are created as specified in ndivs in beam class construct

        ### 
        - `fname:str` = Path / File name to save the data to
        - `fformat:str = 'txt'` = File extension. Default is '.txt'. Supported = `('npy', 'txt', 'gz')`
        """
        meter_unit = BirimiDegistir(JsonEkle.bilgi_oku("Length Unit"),"1").degistir()
        force_unit = BirimiDegistir(JsonEkle.bilgi_oku("Force Unit"),"1").degistir()
        moment_unit = JsonEkle.bilgi_oku("Moment Unit")
        

        fformat = fformat.lower()
        formats = ('npy', 'txt', 'gz')
        if fformat in formats:
            pass
        else:
            raise ValueError(
                f"Unknown file format {fformat}\n Supported formats are: {formats}")

        main_file_name = __main__.__file__.split('/')[-1]
        save_path = __main__.__file__.replace(main_file_name, fname)

        x = self.xbeam[self.xbeam >= 0]
        shear_values = self.shear_values[self.beam_0::]
        moment_values = self.moment_values[self.beam_0::]
        def_values = self.deflection_values[self.beam_0::]
        data_array = np.array((x, shear_values, moment_values, def_values)).T
        self.generate_significant_values()

        print(x)
        support_details = '''Support Conditions:\n'''
        # adding support details for beam
        for rxn in self.reactions_list:
            if isinstance(rxn, Reaction):
                support_details += f"\t\t\t{rxn.pos_sym}-> {rxn.type}\t Position: {rxn.pos} {meter_unit}\n"
            else:
                raise ValueError(f"{rxn} cannot be treated as Reaction object")

        reaction_details = '''Reaction Values:\n'''
        # adding reaction values details
        for (reaction, val) in self.solved_rxns.items():
            reaction_details += f"\t\t\t{reaction} = {f"{val:.2f}"}\n"

        details = f'''
        Beam Description:
        ===================\n 
        Beam Length: {self.length} {meter_unit}
        
        {support_details}
        {reaction_details}

        Significant values:
        ===================\n 
        Shear Force({force_unit}):
        \t Maximum: {self.max_sf}\t\tPosition: {round(self.posx_maxsf,2)} {meter_unit}
        \t Minimum: {self.min_sf}\t\tPosition: {round(self.posx_minsf,2)} {meter_unit}

        Bending Moment{moment_unit}:
        \t Maximum: {self.max_bm}\t\tPosition: {round(self.posx_maxbm,2)} {meter_unit}
        \t Minimum: {self.min_bm}\t\tPosition: {round(self.posx_minbm,2)} {meter_unit}

        Deflection(mm):
        \t Maximum: {self.max_df}\t\tPosition: {round(self.posx_maxdf,2)} {meter_unit}
        \t Minimum: {self.min_df}\t\tPosition: {round(self.posx_mindf,2)} {meter_unit}
        \n
=======================================================================================

        x\t\t\t Shear Force\t\t\t Bending Moment\t\t\t Deflection
        '''
        np.savetxt(save_path+'.'+fformat, data_array,
                   delimiter="\t\t\t", header=details, fmt="\t%.3f")

class Load:
    '''
    Load class 

    ### Attributes:
    `pos(float)`: `unit:meter` position of that netload with respect to beam coordinates's origin
    `load(float)`: `unit:kN` net load of that load type(for point load that is point load value, 
                            but it will be different 
                            for other loads like uvl and udl)
    `inverted(bool)=False`: Default direction of positive net load is in positive direction of y-axes
    - by default: `inverted = False` (load is facing upward)
    - use `inverted=True` to indicate load is in downward direction

    '''

    def __init__(self, pos: float, load: float, inverted=False, **kwargs):
        self.pos = pos
        self.inverted = inverted
        if self.inverted:
            self.load = -1*load
        else:
            self.load = load

class PointLoad(Load):
    """
    ## Description 
    Subclass of Class Load

    ### Attributes:
    `pos, load, inverted`: inherit from super class `Load`
    `inclination(float)=90`: `unit=degree` represents angle made by direction of net load with positive direction of beam's x axis
                            inclination will be positive for counter clockwise direction
                            put negative inclination if you want to take angle in clockwise direction
    `load_x`: component of net load value in positive direciton of beam's x-axis
    `load_y`: component of net load value in positive y-direciton(upward direction)
    """

    def __init__(self, pos: float, load: float, inverted: bool = False, inclination=90, **kwargs):
        super().__init__(pos, load, inverted, **kwargs)
        # self.var = sp.symbols(var) #might require variable for load too.
        # inclination of point load with positive direction of beam axis
        self.inclination = inclination
        self.load_x = round(
            self.load*np.cos(self.inclination*np.pi/180), ndigits=4)
        self.load_y = round(
            self.load*np.sin(self.inclination*np.pi/180), ndigits=4)
        
class UDL:
    """
    ## Description
    UDL is type of load that is combinaiton of infinite points load over certain length acting transverse to beam

    ### Attributes:
    `start(float)`:Start position of UDL
    `loadpm(float)`: Load Per meter of udl
    `span(float)`: Total length of udl
    `inverted(bool) = True`: UDL facing downwards on beam,
                                use `inverted=False` for upside udl
    `self.netload(float)`: total effective load of udl
    `self.pos(float)`: position of effective load from beam origin
    """

    def __init__(self, start: float, loadpm: float, span: float, inverted: bool = True, **kwargs):
        self.start = start  # x coordinate of left edge of udl
        self.span = span  # total length of udl
        self.end = start + span
        self.inverted = inverted
        if self.inverted:
            self.loadpm = -1*loadpm
        else:
            self.loadpm = loadpm

        self.netload = self.loadpm * self.span  # netload of udl
        self.pos = self.start + self.span/2  # position of effective load of udl

class UVL:
    """
    ## Description
    It is that load whose magnitude varies along the loading length with a constant rate. 
    Uniformly varying load is further divided into two types;
        1. Triangular Load
        2. Trapezoidal Load

    ### Arguments
    1. `start:float` = Start position of uvl from beam's origin along x-axis of beam coordinate system
    2. `startload:float` = `unit: kN/m` = Starting load/m value of uvl
    3. `span:float` = Total length of uvl object
    4. `endload:float` = Ending load/m value of uvl object
    5. `inverted:bool= True` : Default=`True` Inverts the uvl object

    ### Attributes
    - `self.end` = End coordinate of uvl object
    - `self.tload` = Net load value of upper triangular part of trapezoidal or triangular load
    - `self.rload` = Net load value of lower rectangular part of trapezoidal load itself
    - `self.netload` = Net load of whole uvl object itself. `netload = tload + rload`
    - `self.netpos` = Net position(coordinates) where net load of uvl acts
    """

    def __init__(self, start: float, startload: float, span: float, endload: float, inverted: bool = True, **kwargs):
        self.start = start
        self.span = span
        self.end = span+start
        self.inverted = inverted

        if self.inverted:
            self.startload = -1*startload
            self.endload = -1*endload
        else:
            self.startload = startload
            self.endload = endload

        # gradient of uvl:
        self.gradient = (self.endload-self.startload)/span
        if startload > endload:
            self.zero_load = startload / abs(self.gradient)

        # for upper triangular part: 1/2*b*h
        self.tload = self.span*abs(self.endload-self.startload)/2
        # for lowe rectangular part: b*h
        self.rload = self.span*min(abs(self.startload), abs(self.endload))

        self.netload = self.span*(self.startload + self.endload)/2  # net load

        if abs(self.endload) > abs(self.startload):
            self.pos = self.start + \
                (2*self.tload*self.span/3 + self.rload*self.span/2)/abs(self.netload)
        else:
            self.pos = self.start + \
                (self.tload*self.span/3 + self.rload*self.span/2)/abs(self.netload)

class Reaction:
    """
    ## Description
        Reactions are given by supports. 3 types of supports are defined for now
        `hinge`, `roller` and `fixed` support.

   ### Arguments
    - `pos(float)`: position of reaction
    - `type(str)`: any one of `('roller'`,`'hinge'`,`'fixed')` or `('r'`,`'h'`,`'f')` Representing support condition at that point.
    - `pos_sym(str)`: Symbolic variable to represent support location name 

    ### Attributes
    - `rx_val, ry_val, mom_val`: variables to store numerical values for reaction loads and moments
    - `rx_var, ry_var, mom_var`: symbolic variables to store symbolic values for reactions
    """

    def __init__(self, pos: float, type: str, pos_sym: str):
        self.pos = pos
        self.pos_sym = pos_sym
        # possible reaction values(initialize them as zeros):
        self.rx_val = 0
        self.ry_val = 0
        self.mom_val = 0

        self.type = type.lower()
        if self.type == 'roller' or self.type == 'r':
            self.type = 'roller'
            # symbolic variable for that roller support
            self.ry_var = sp.Symbol(f"R_{pos_sym}_y")
        elif self.type == 'hinge' or self.type == 'h':
            self.type = 'hinge'
            self.rx_var = sp.Symbol(f"R_{pos_sym}_x")
            self.ry_var = sp.Symbol(f"R_{pos_sym}_y")
        elif self.type == 'fixed' or self.type == 'f':
            self.type = 'fixed'
            self.rx_var = sp.Symbol(f"R_{pos_sym}_x")
            self.ry_var = sp.Symbol(f"R_{pos_sym}_y")
            self.mom_var = sp.Symbol(f"M_{pos_sym}")
        else:
            raise ValueError(f"Unidentified support type: {self.type}")

class PointMoment:
    """
    ## Description
    Pure moment that act at point

    ### Attributes
    `pos`: location of that point moment from beam's origin
    `mom`: value of that point moment
    `ccw`(bool)=`False` : counterclockwise direciton is positive value of moment, 
                by defalut: ccw=False and given moment is positive

    """

    def __init__(self, pos: float, mom: float, ccw: bool = True):
        self.pos = pos
        self.ccw = ccw
        if self.ccw:
            self.mom = mom
        else:
            self.mom = -1*mom

class Hinge:
    """
    ## Description
    (Hinge) Internal hinges are provided in a structure to reduce statical indeterminacy of the structure. 
    Bending moment at internal hinge is always zero. 
    Internal hinge makes structure more flexible. 
    It allows structure to move which reduces the reactive stresses.

    ### Attributes
    1. `pos:float` = Position of that internal hinge from origin of beam coordinate system
    2. `side:str = 'l'` : Accepted Values = `('r', 'right', 'l', 'left')`, Default Value = `'l'`
        - This side specifies which side of loads to take in order to take moment of that loads about hinge.
    """

    def __init__(self, pos: float, side: str = 'l'):
        self.pos = pos
        if side.lower() in ('r', 'right', 'l', 'left'):
            self.side = side.lower()
        else:
            raise ValueError(
                f"Unknown side attribute '{side}'\n Use 'l' for left and 'r' for right")



