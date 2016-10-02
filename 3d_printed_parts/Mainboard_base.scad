PCB_size = 50;
PCB_thick = 1.5;
extraxy=0.7;
PCB_height = 8;
oah = 30-1.75;
wall = 2;

hole_dim = (PCB_size-2*4)/2+0.3; //shouldn't need the 0.3 but it seems to. 

difference(){
    translate([-PCB_size/2-wall-extraxy/2,-PCB_size/2-wall-extraxy/2,0])
        v_rounded_cube([PCB_size+2*wall+extraxy,PCB_size+2*wall+extraxy,oah] ,5);
    
    translate([-PCB_size/2-wall-extraxy/2,-PCB_size/2-wall-extraxy/2,0])
    translate([wall,wall,wall])
        v_rounded_cube([PCB_size+extraxy,PCB_size+extraxy,2*oah],3 );
    
    //USB cutout
    translate([-PCB_size/2+7,-6-PCB_size/2,PCB_height+PCB_thick])
    cube([12,12,11]);
    //molex cutout
    translate([-23.1+PCB_size/2-6.7,-6-PCB_size/2,PCB_height+PCB_thick])
    cube([23.1,10.3,9.3]);
    //rj45 cutout
    translate([-15.5+PCB_size/2-9.7,-6+PCB_size/2,PCB_height+PCB_thick])
    cube([15.5,10,13.2]);
}
for (ii = [-hole_dim,hole_dim]){
    for (jj = [-hole_dim,hole_dim]) {
        translate([ii,jj]) mount_hole(PCB_height);
    }
}

module mount_hole(h,$fn=30) {
    difference() {
        cylinder(r=5,h=h);
        cylinder(d=2.8,h=h);
    }
}

module v_rounded_cube(xyz,r,$fn=30) {
  z = xyz[2];
  y = xyz[1];
  x = xyz[0];
  translate([r,r])
  hull() {
    cylinder(h=z,r=r);
    translate([0,y-2*r])
    cylinder(h=z,r=r);
    translate([x-2*r,0])
    cylinder(h=z,r=r);
    translate([x-2*r,y-2*r])
    cylinder(h=z,r=r);
  }
}