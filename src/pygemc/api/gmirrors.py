# =======================================
# gemc mirrors definition
#
# This file defines a GMirror class that holds the parameters needed to define an optical
# boundary in gemc. Any type of optical boundary is described as a "mirror", regardless of
# its use or reflective quality.
#
# A GMirror is instantiated with the mirror name. The following members are mandatory and
# checked at publish time:
#
# - type:   the surface type (see below). Example: "dielectric_dielectric" or "dielectric_metal"
# - finish: the type of finish of the optical surface (see below). Example: "polishedfrontpainted"
# - model:  the optical model to use for the surface (see below)
# - border: "SkinSurface" if the optical boundary represents the entire outside surface of a
#           volume. For a border surface defined as the contact area between two neighboring
#           volumes, use the name of the bordering volume.
#
# The boundary optical properties come from either:
#
# - matOptProps: the name of a material with optical properties to use as the boundary
#                properties. The material does not have to be the same as either bordering
#                volume, i.e., a thin paint.
#
# or the explicit tables, each a string of values evaluated at photonEnergy:
#
# - photonEnergy:      a list of photon energies at which to evaluate the optical properties
# - indexOfRefraction: boundary material refractive indices
# - reflectivity:      boundary material reflectivities
# - efficiency:        photoelectric absorption efficiencies. Used in "dielectric_metal"
#                      boundaries where the photon is either reflected or absorbed by the
#                      metal with this efficiency. Can be used as the quantum efficiency of
#                      a PMT.
# - specularlobe, specularspike, backscatter: scattering properties of a rough surface
# - transmittance:     probability that the photon is transmitted through the surface
#                      (e.g. a semi-transparent, half-silvered mirror)
# - sigmaAlpha: roughness parameter of the surface (unified model)
#
# A volume is associated to a mirror through the GVolume `mirror` field, which names the
# GMirror applied to that volume surface.

# =================================================================
# Available finish in materials/include/G4OpticalSurface.hh:
#
# polished,                    // smooth perfectly polished surface
# polishedfrontpainted,        // smooth top-layer (front) paint
# polishedbackpainted,         // same is 'polished' but with a back-paint
#
# ground,                      // rough surface
# groundfrontpainted,          // rough top-layer (front) paint
# groundbackpainted,           // same as 'ground' but with a back-paint
#
# polishedlumirrorair,         // mechanically polished surface, with lumirror
# polishedlumirrorglue,        // mechanically polished surface, with lumirror & meltmount
# polishedair,                 // mechanically polished surface
# polishedteflonair,           // mechanically polished surface, with teflon
# polishedtioair,              // mechanically polished surface, with tio paint
# polishedtyvekair,            // mechanically polished surface, with tyvek
# polishedvm2000air,           // mechanically polished surface, with esr film
# polishedvm2000glue,          // mechanically polished surface, with esr film & meltmount
#
# etchedlumirrorair,           // chemically etched surface, with lumirror
# etchedlumirrorglue,          // chemically etched surface, with lumirror & meltmount
# etchedair,                   // chemically etched surface
# etchedteflonair,             // chemically etched surface, with teflon
# etchedtioair,                // chemically etched surface, with tio paint
# etchedtyvekair,              // chemically etched surface, with tyvek
# etchedvm2000air,             // chemically etched surface, with esr film
# etchedvm2000glue,            // chemically etched surface, with esr film & meltmount
#
# groundlumirrorair,           // rough-cut surface, with lumirror
# groundlumirrorglue,          // rough-cut surface, with lumirror & meltmount
# groundair,                   // rough-cut surface
# groundteflonair,             // rough-cut surface, with teflon
# groundtioair,                // rough-cut surface, with tio paint
# groundtyvekair,              // rough-cut surface, with tyvek
# groundvm2000air,             // rough-cut surface, with esr film
# groundvm2000glue             // rough-cut surface, with esr film & meltmount

# Available models in materials/include/G4OpticalSurface.hh:
#
# glisur,                      // original GEANT3 model
# unified,                     // UNIFIED model
# LUT                          // Look-Up-Table model

# Available surface types in materials/include/G4SurfaceProperty.hh
#
# dielectric_metal,            // dielectric-metal interface
# dielectric_dielectric,       // dielectric-dielectric interface
# dielectric_LUT,              // dielectric-Look-Up-Table interface
# firsov,                      // for Firsov Process
# x_ray                        // for x-ray mirror process

# Border Volume Types:
#
# SkinSurface: surface of a volume
# Border Surface: surface between two volumes (second volume must exist)

# =================================================================

import sys

# mandatory fields, checked at publish time
WILLBESETSTRING = 'WILLBESET'

# for optional fields
NOTASSIGNED = None

from .gsqlite import populate_sqlite_mirrors


# Mirror class definition
class GMirror():
	def __init__(self, name):
		# mandatory fields. Checked at publish time
		self.name   = name
		self.type   = WILLBESETSTRING
		self.finish = WILLBESETSTRING
		self.model  = WILLBESETSTRING
		self.border = WILLBESETSTRING

		# optional fields
		self.description = NOTASSIGNED

		# boundary optical properties: either the name of a material with optical
		# properties, or the explicit tables below
		self.matOptProps       = NOTASSIGNED
		self.photonEnergy      = NOTASSIGNED
		self.indexOfRefraction = NOTASSIGNED
		self.reflectivity      = NOTASSIGNED
		self.efficiency        = NOTASSIGNED
		self.specularlobe      = NOTASSIGNED
		self.specularspike     = NOTASSIGNED
		self.backscatter       = NOTASSIGNED
		self.transmittance     = NOTASSIGNED
		self.sigmaAlpha        = NOTASSIGNED

	def check_validity(self):
		if self.type == WILLBESETSTRING:
			sys.exit(' Error: type not defined for GMirror ' + str(self.name))
		if self.finish == WILLBESETSTRING:
			sys.exit(' Error: finish not defined for GMirror ' + str(self.name))
		if self.model == WILLBESETSTRING:
			sys.exit(' Error: model not defined for GMirror ' + str(self.name))
		if self.border == WILLBESETSTRING:
			sys.exit(' Error: border not defined for GMirror ' + str(self.name))
		# the boundary needs optical properties: a material name or the explicit tables
		if self.matOptProps is NOTASSIGNED and self.photonEnergy is NOTASSIGNED:
			sys.exit(' Error: no optical properties defined for GMirror ' + str(self.name)
			         + ': set matOptProps or photonEnergy with the properties tables')
		if self.matOptProps is NOTASSIGNED:
			if (self.indexOfRefraction is NOTASSIGNED and self.reflectivity is NOTASSIGNED
					and self.efficiency is NOTASSIGNED):
				sys.exit(' Error: photonEnergy is defined for GMirror ' + str(self.name)
				         + ' but no property (indexOfRefraction, reflectivity, efficiency) is')

	def entry_to_ascii(self, v):
		# Normalize Python-side 'empty' values for ascii output
		if v is None:
			return 'NULL'
		if isinstance(v, (list, tuple)):
			return ' '.join(map(str, v))
		return str(v).strip()

	def publish(self, configuration):
		self.check_validity()
		if hasattr(configuration, "record_current_variation_run"):
			configuration.record_current_variation_run()

		if configuration.factory == 'ascii':
			fileName = configuration.mirFileName
			configuration.nmirrors += 1
			with open(fileName, 'a+') as dn:
				ea = self.entry_to_ascii
				line  = "%20s  |" % ea(self.name)
				line += "%40s  |" % ea(self.description)
				line += "%24s  |" % ea(self.type)
				line += "%20s  |" % ea(self.finish)
				line += "%10s  |" % ea(self.model)
				line += "%25s  |" % ea(self.border)
				line += "%25s  |" % ea(self.matOptProps)
				line += "%60s  |" % ea(self.photonEnergy)
				line += "%30s  |" % ea(self.indexOfRefraction)
				line += "%30s  |" % ea(self.reflectivity)
				line += "%30s  |" % ea(self.efficiency)
				line += "%30s  |" % ea(self.specularlobe)
				line += "%30s  |" % ea(self.specularspike)
				line += "%30s  |" % ea(self.backscatter)
				line += "%30s  |" % ea(self.transmittance)
				line += "%10s  |\n" % ea(self.sigmaAlpha)
				dn.write(line)

		elif configuration.factory == 'sqlite':
			configuration.nmirrors += 1
			populate_sqlite_mirrors(self, configuration)

		if int(configuration.verbosity) > 0:
			print(f"  + GMirror {self.name} uploaded successfully for variation "
			      f"<{configuration.variation}>, run {configuration.runno}")
