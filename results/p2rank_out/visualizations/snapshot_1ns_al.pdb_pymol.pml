from pymol import cmd,stored

set depth_cue, 1
set fog_start, 0.4

set_color b_col, [36,36,85]
set_color t_col, [10,10,10]
set bg_rgb_bottom, b_col
set bg_rgb_top, t_col      
set bg_gradient

set  spec_power  =  200
set  spec_refl   =  0

load "data/snapshot_1ns_al.pdb", protein
create ligands, protein and organic
select xlig, protein and organic
delete xlig

hide everything, all

color white, elem c
color bluewhite, protein
#show_as cartoon, protein
show surface, protein
#set transparency, 0.15

show sticks, ligands
set stick_color, magenta




# SAS points

load "data/snapshot_1ns_al.pdb_points.pdb.gz", points
hide nonbonded, points
show nb_spheres, points
set sphere_scale, 0.2, points
cmd.spectrum("b", "green_red", selection="points", minimum=0, maximum=0.7)


stored.list=[]
cmd.iterate("(resn STP)","stored.list.append(resi)")    # read info about residues STP
lastSTP=stored.list[-1] # get the index of the last residue
hide lines, resn STP

cmd.select("rest", "resn STP and resi 0")

for my_index in range(1,int(lastSTP)+1): cmd.select("pocket"+str(my_index), "resn STP and resi "+str(my_index))
for my_index in range(1,int(lastSTP)+1): cmd.show("spheres","pocket"+str(my_index))
for my_index in range(1,int(lastSTP)+1): cmd.set("sphere_scale","0.4","pocket"+str(my_index))
for my_index in range(1,int(lastSTP)+1): cmd.set("sphere_transparency","0.1","pocket"+str(my_index))



set_color pcol1 = [0.361,0.576,0.902]
select surf_pocket1, protein and id [3570,3656,3585,3589,2989,2993,3652,3587,3014,3018,3011,2933,3670,4671,4674,4675,3649,4708,4712,3635,6254,6250,6258,2134,2983,2135,4700,4704,4650,4678,4681,4683,4682,5782,5771,5776,5780,5788,5803,5806,5807,5811,5813,6245,6269,6276,6261,6267,551,557,615,851,855,797,843,846,849,847,563,496,567,487,491,493,497,653,660,570,656,777,4772,978,980,5318,5324,5328] 
set surface_color,  pcol1, surf_pocket1 
set_color pcol2 = [0.278,0.322,0.702]
select surf_pocket2, protein and id [1953,3004,1924,1935,1955,1961,1965,1981,1982,3057,3061,1983,3003,3140,3141,3144,3198,3145,3146,3200,3160,3213,2958,3051,3065,3005,3077] 
set surface_color,  pcol2, surf_pocket2 
set_color pcol3 = [0.467,0.361,0.902]
select surf_pocket3, protein and id [5310,5311,5314,5321,5322,5326,5328,5789,5793,5826,5856,7995,7996,8016,5890,7950,7655,7659,7903,7909,7949] 
set surface_color,  pcol3, surf_pocket3 
set_color pcol4 = [0.490,0.278,0.702]
select surf_pocket4, protein and id [2874,4459,5189,4463,4454,1795,4418,6464,6476,6478,6484,6565,6489,1751,5193,6451,6558] 
set surface_color,  pcol4, surf_pocket4 
set_color pcol5 = [0.792,0.361,0.902]
select surf_pocket5, protein and id [4851,4864,4866,4868,4810,3724,3759,3763,3744,4618,4622,4870,3720,3727,3944,4283,3856,4804,4805,4808,4757,4289] 
set surface_color,  pcol5, surf_pocket5 
set_color pcol6 = [0.702,0.278,0.659]
select surf_pocket6, protein and id [2450,2451,2452,2339,2353,2356,2368,2367,2374,6818,6823,2379,2381,6817,2465,2469,6781,6771,6773,6757,6758] 
set surface_color,  pcol6, surf_pocket6 
set_color pcol7 = [0.902,0.361,0.682]
select surf_pocket7, protein and id [7720,6749,6799,6963,6715,7703,7707,6964,6997,6991,7616,7620] 
set surface_color,  pcol7, surf_pocket7 
set_color pcol8 = [0.702,0.278,0.408]
select surf_pocket8, protein and id [4678,4681,4683,5266,5269,4643,5782,5314,5317,5318,5321,5324] 
set surface_color,  pcol8, surf_pocket8 
set_color pcol9 = [0.902,0.361,0.361]
select surf_pocket9, protein and id [7999,8057,8068,8073,8076,8079,8117,7943,7896,7944,7946,7940,7893,7897,7996,8016,7950,8045,8047] 
set surface_color,  pcol9, surf_pocket9 
set_color pcol10 = [0.702,0.408,0.278]
select surf_pocket10, protein and id [3621,823,878,882,895,3111,3094,3103,3100,3106,829,3068,3082,3086,3090,3828] 
set surface_color,  pcol10, surf_pocket10 
set_color pcol11 = [0.902,0.682,0.361]
select surf_pocket11, protein and id [2726,2803,2807,2797,2725,2796,3407,3420,3453,3457,2688,2791] 
set surface_color,  pcol11, surf_pocket11 
set_color pcol12 = [0.702,0.659,0.278]
select surf_pocket12, protein and id [5841,6647,6649,5847,5835,7572,7129] 
set surface_color,  pcol12, surf_pocket12 
   

deselect

orient
