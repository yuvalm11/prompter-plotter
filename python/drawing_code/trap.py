# TRAP:
# (365,305) (235, 305) (0, 305) (-130, 305)
#           (235,   0) (0,   0)
for _ in range(3):
    await controller.goto([-130,305,0], 50)
    await controller.goto([0,0,0], 50)
    await controller.goto([235,0,0], 50)
    await controller.goto([365, 305, 0], 50)
for _ in range(3):
    await controller.goto([0,0,0], 50)
    await controller.goto([235,0,0], 50)
    await controller.goto([-130,305,0], 50)
    await controller.goto([365, 305, 0], 50)