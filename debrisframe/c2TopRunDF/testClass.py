

class RasterioClass():
    def __init__(self,raster):
        self.raster = raster

    def avaframe(self):
        a = self.raster[0,0]
        b = self.raster[0,1]
        c = self.raster[2,0]
        d = self.raster[2,1]
        e = self.raster[3,0]
        f = self.raster[3,1]

        return a,b, c, d, e, f

    def topRun(self):
        a = self.raster.read(1)[0,0]
        b = self.raster.read(1)[0,1]
        c = self.raster.read(1)[2,0]
        d = self.raster.read(1)[2,1]
        e = self.raster.read(1)[3,0]
        f = self.raster.read(1)[3,1]

        return a,b, c, d, e, f
