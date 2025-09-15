# TRAP:
# (365,305) (235, 305) (0, 305) (-130, 300)
#           (235,   0) (0,   0)
for _ in range(3):
    await machine.queue_planner.goto_via_queue([-130,305,0], draw_rate)
    await machine.queue_planner.goto_via_queue([0,0,0], draw_rate)
    await machine.queue_planner.goto_via_queue([235,0,0], draw_rate)
    await machine.queue_planner.goto_via_queue([365, 305, 0], draw_rate)
for _ in range(3):
    await machine.queue_planner.goto_via_queue([0,0,0], draw_rate)
    await machine.queue_planner.goto_via_queue([235,0,0], draw_rate)
    await machine.queue_planner.goto_via_queue([-130,305,0], draw_rate)
    await machine.queue_planner.goto_via_queue([365, 305, 0], draw_rate)