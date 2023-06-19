mdp

const int street_length = 60;
const int min_street_length = 10;
const int sidewalk_height = 2;

const int crosswalk_pos = 45;
const int crosswalk_width = 10;
const int crosswalk_height = 11;

const int world_height = (sidewalk_height * 2) + crosswalk_height;

const int max_speed = 5;

// block properties, don't eliminate for no visiblity, used in some strategies as for nov 22
const int block_height = 2;
const int block_width = 5;
const int block_x1 = crosswalk_pos - 5; // {bottom_corner_x}
const int block_y1 = sidewalk_height; // {bottom_corner_y}
const int block_x2 = block_x1 + block_width; // {top_corner_x}
const int block_y2 = sidewalk_height + block_height; //{top_corner_y}
 
// car properties
const int car_height = 2; // was two
const int car_width = 3;
const int car_y = 5; // {car_y}

global turn : [0..2] init 0;
global crashed :[0..1] init 0;

// crash can only happen when car has just moved (turn =2 & car_v > 0)
// in that case, a crash happens if the tip of the cad (car_x + car_height) moves from being behind to being in front of pedestrian
formula crash = (turn=2) &  (car_v > 0) & ((ped_x >= car_x+car_width-car_v) & (ped_x <= car_x + car_width)) & ((ped_y >= car_y) & (ped_y <= car_y + car_height));

label "crash" = crash;
label "givereward" = ((finished=0) & (car_x = street_length));

formula dist_x = max(ped_x-car_x, car_x - ped_x);
formula dist_y = max(ped_y - car_y, car_y - ped_y);
formula dist = dist_x + dist_y;
formula safe_dist = dist > 15;

formula wait_prob = (crosswalk_pos - ped_x) / 10;


formula car_close_crosswalk = ((car_x > crosswalk_pos - 10) & (car_x < crosswalk_pos + crosswalk_width));
formula car_close_block = ((car_x > block_x1 - 5) & (car_x < block_x2));
formula car_close_ped = (ped_x - car_x < 2*car_v);
formula car_close_ped_rv = (ped_x - car_x < 2*(car_v-1)); // rv: reckless version
formula is_within_shot = (ped_y >= car_y) & (ped_y <= car_y + car_height);

// formula allowed_to_brake = (car_v > 0) & (ped_x > car_x) & (dist < 15);
formula allowed_to_brake = ((car_v > 3) & (dist < 15)) | ((car_v > 0) & (dist < 10)) | (dist < 5);
formula allowed_to_noop =  (car_v > 0) | (dist < 5);

// Constants used later in the car module
formula is_slippery = (car_x > 40) & (car_x < 60);

const double slippery_factor = 2;

const double acc2_prob = 0.45;
const double acc1_prob = 0.45;
const double acc0_prob = 1-acc1_prob-acc2_prob;

const double acc2_prob_s = 0.225;
const double acc1_prob_s = 0.225;
const double acc0_prob_s = 1-acc1_prob_s-acc2_prob_s;

const double brk2_prob = 0.45;
const double brk1_prob = 0.45;
const double brk0_prob = 1-brk1_prob-brk2_prob;

const double brk2_prob_s = 0.225;
const double brk1_prob_s = 0.225;
const double brk0_prob_s = 1-brk1_prob_s-brk2_prob_s;

const double noop0 = 0.9;
const double noop1 = 0.1;

module Car
car_x : [min_street_length..street_length] init 25; //{car_x};
car_v : [0..max_speed] init 0; //{car_v}
finished : [0..1] init 0;

    // changes the visibility variable so we know when the car is able/unable to see ped
    [] (turn = 0) -> (turn'=1);

	[accelerate] (turn = 1) & (finished=0) & (car_x < street_length) & (crashed=0) & (!is_slippery) -> // Accelerate
	acc2_prob: (car_v' = min(max_speed, car_v + 2))&(car_x' = min(street_length, car_x + min(max_speed, car_v + 2)))&(turn' = 2) +
	acc1_prob: (car_v' = min(max_speed, car_v + 1))&(car_x' = min(street_length, car_x + min(max_speed, car_v + 1)))&(turn' = 2) +
	acc0_prob: (car_x' = min(street_length, car_x + car_v + 0))&(turn' = 2);

	[accelerateSlippery] (turn = 1) & (finished=0) & (car_x < street_length) & (crashed=0) & (is_slippery) -> // Accelerate
	acc2_prob_s: (car_v' = min(max_speed, car_v + 2))&(car_x' = min(street_length, car_x + min(max_speed, car_v + 2)))&(turn' = 2) +
	acc1_prob_s: (car_v' = min(max_speed, car_v + 1))&(car_x' = min(street_length, car_x + min(max_speed, car_v + 1)))&(turn' = 2) +
	acc0_prob_s: (car_x' = min(street_length, car_x + car_v + 0))&(turn' = 2);

	[brake] (turn = 1) & (finished=0) & (car_x < street_length) & (crashed=0) & (allowed_to_brake) & (!is_slippery) -> //& (car_v > 0) -> // Brake
	brk2_prob: (car_v' = max(0, car_v - 2))&(car_x' = min(street_length, car_x + max(0, car_v - 2)))&(turn' = 2) + 
	brk1_prob: (car_v' = max(0, car_v - 1))&(car_x' = min(street_length, car_x + max(0, car_v - 1)))&(turn' = 2) +
	brk0_prob: (car_x' = min(street_length, car_x + car_v + 0))&(turn' = 2);

	[brakeSlippery] (turn = 1) & (finished=0) & (car_x < street_length) & (crashed=0) & (allowed_to_brake) & (is_slippery) -> //& (car_v > 0) -> // Brake
	brk2_prob_s: (car_v' = max(0, car_v - 2))&(car_x' = min(street_length, car_x + max(0, car_v - 2)))&(turn' = 2) + 
	brk1_prob_s: (car_v' = max(0, car_v - 1))&(car_x' = min(street_length, car_x + max(0, car_v - 1)))&(turn' = 2) +
	brk0_prob_s: (car_x' = min(street_length, car_x + car_v + 0))&(turn' = 2);

	[brakeNoop] (turn = 1) & (finished=0) & (car_x < street_length) & (crashed=0) & (!allowed_to_brake) -> //& (car_v > 0) -> // Brake
	noop0: (car_x' = min(street_length, car_x + max(0, car_v)))&(turn' = 2) +
	noop1: (car_v' = max(0, car_v - 1))&(car_x' = min(street_length, car_x + max(0, car_v - 1)))&(turn' = 2);
	
	[nop] (turn = 1) & (finished=0) & (car_x < street_length) & (crashed=0) & (allowed_to_noop)-> // Stays the same speed
	noop0: (car_x' = min(street_length, car_x + max(0, car_v)))&(turn' = 2) +
	noop1: (car_v' = max(0, car_v - 1))&(car_x' = min(street_length, car_x + max(0, car_v - 1)))&(turn' = 2);
	
	[nopAccel] (turn = 1) & (finished=0) & (car_x < street_length) & (crashed=0) & (!allowed_to_noop) & (!is_slippery)-> // Stays the same speed
	acc2_prob: (car_v' = min(max_speed, car_v + 2))&(car_x' = min(street_length, car_x + min(max_speed, car_v + 2)))&(turn' = 2) +
	acc1_prob: (car_v' = min(max_speed, car_v + 1))&(car_x' = min(street_length, car_x + min(max_speed, car_v + 1)))&(turn' = 2) +
	acc0_prob: (car_x' = min(street_length, car_x + car_v + 0))&(turn' = 2);

	[nopAccelSlippery] (turn = 1) & (finished=0) & (car_x < street_length) & (crashed=0) & (!allowed_to_noop) & (is_slippery)-> // Stays the same speed
	acc2_prob: (car_v' = min(max_speed, car_v + 2))&(car_x' = min(street_length, car_x + min(max_speed, car_v + 2)))&(turn' = 2) +
	acc1_prob: (car_v' = min(max_speed, car_v + 1))&(car_x' = min(street_length, car_x + min(max_speed, car_v + 1)))&(turn' = 2) +
	acc0_prob: (car_x' = min(street_length, car_x + car_v + 0))&(turn' = 2);

	
	[] (turn = 1) & (finished = 0) & ((car_x = street_length) | (crashed=1)) -> (finished'=1);
	[] (turn = 1) & (finished = 1) -> true;
	
	 
	 
endmodule

// formula move_xx_yy_zz = xx: (ped_x' = min(street_length, ped_x+1))&(turn'=0) + yy: (ped_y'=min(world_height, ped_y+1))&(turn'=0) + zz: (turn'=0);
formula is_on_sidewalk = (ped_y <= sidewalk_height) | (ped_y >= sidewalk_height + crosswalk_height);
formula is_on_sidewalk_rv = (ped_y <= sidewalk_height+1) | (ped_y >= sidewalk_height + crosswalk_height); // rv : reckless version
formula blocked_path = (ped_x >= block_x1) & (ped_x <= block_x2);
formula on_crosswalk = (ped_x >= crosswalk_pos) & (ped_x <= crosswalk_pos+crosswalk_height);

// Hesitant pedestrian takes into account if there is danger to cross or to stay.
// Can only affect when pedestrian is not on sidewalk anymore
formula danger_to_cross = (car_close_ped) & (car_v > 2) & (car_y - ped_y = 1);
formula danger_to_stay = (car_close_ped) & (car_v > 2) & (car_y - ped_y < 1) & (car_y+car_height >= ped_y);
const double hesitant_factor = 0.4;

module Pedestrian
	ped_x : [min_street_length..street_length] init (crosswalk_pos - 5); // {person_x}
	ped_y : [0..world_height] init 0; // {person_y}

	// When pedestrian is not on sidewalk anymore, can only stop or cross, cannot go back
	// If hesitant, checks if it is unsafe to stop or cross and reduces probabilities by hesitant_prob
	[] (turn = 2)&(!crash)&(!is_on_sidewalk)&(!danger_to_cross)&(!danger_to_stay) -> 0.7: (ped_y'=min(world_height, ped_y+1))&(turn'=0) + 0.3: (turn'=0);
	[] (turn = 2)&(!crash)&(!is_on_sidewalk)&(danger_to_cross) -> 0.7*hesitant_factor: (ped_y'=min(world_height, ped_y+1))&(turn'=0) + 1-0.7*hesitant_factor: (turn'=0);
	[] (turn = 2)&(!crash)&(!is_on_sidewalk)&(danger_to_stay) -> 1-0.3*hesitant_factor: (ped_y'=min(world_height, ped_y+1))&(turn'=0) + 0.3*hesitant_factor: (turn'=0);
	
	// When pedestrian is on sidewalk and crosswalk, starts crossing with high probability
	[] (turn=2)&(!crash)&(is_on_sidewalk)&(on_crosswalk) ->
	0.45: (ped_x' = min(street_length, ped_x+1))&(turn'=0) + 0.45: (ped_y'=min(world_height, ped_y+1))&(turn'=0) + 0.1: (turn'=0);

	// When pedestrian is on sidewalk and not crosswalk, starts crossing with low probability
	[] (turn=2)&(!crash)&(is_on_sidewalk)&(!on_crosswalk) ->
	0.8: (ped_x' = min(street_length, ped_x+1))&(turn'=0) + 0.1: (ped_y'=min(world_height, ped_y+1))&(turn'=0) + 0.1: (turn'=0);

	// If car has crashed, simulation goes to end
	[] crash -> (crashed'=1)&(turn'=1);

endmodule