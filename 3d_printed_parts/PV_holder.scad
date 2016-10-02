size =50;
tap_hole_632 = 2.85; //2.95=tap hole for 6-32.  2.85 = self taping hole for M3
difference() {
  union() {
    translate([-size/2,-size/2])
    v_rounded_cube([size,size,3],r=4);
    for (ii=[-33/2,33/2]) {
      translate([ii-9/2,-15/2,0]) v_rounded_cube([9,15,40],r=3);
    }
  }

  translate([-size/2,-size/2])
  for (ii = [4,size-4]) {
    for (jj = [4,size-4]) {
      translate([ii,jj,0]) cylinder(h=10,d=3.5 , center=true,$fn=30);
    }
  }
  cylinder(h=10,d=24 , center=true);
  for (ii=[-33/2,33/2]) {
    translate([ii,0,0]) cylinder(h=44,d=tap_hole_632 , center=false,$fn=40);
  }
  translate([-size/2+8,size/2-6.5,-1])
  cube([6,3,10]);
  translate([-size/2+8+6+0.1*25.4,size/2-6.5,-1])
  cube([6,3,10]);
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