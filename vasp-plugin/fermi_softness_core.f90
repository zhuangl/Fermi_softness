! SPDX-License-Identifier: BSD-3-Clause
! Original VASP-independent kernel. No VASP source is included.
module fermi_softness_core
  use, intrinsic :: iso_fortran_env, only: real64
  use, intrinsic :: iso_c_binding, only: c_double
  use, intrinsic :: ieee_arithmetic, only: ieee_is_finite, ieee_value, ieee_quiet_nan
  implicit none
  private
  public :: fermi_weight, accumulate_softness, fs_weight_c
contains
  pure elemental function fermi_weight(energy, mu, kt) result(weight)
    real(real64), intent(in) :: energy, mu, kt
    real(real64) :: weight, q
    if (.not. ieee_is_finite(kt) .or. kt <= 0.0_real64 .or. &
        .not. ieee_is_finite(energy) .or. .not. ieee_is_finite(mu)) then
      weight = ieee_value(0.0_real64, ieee_quiet_nan)
      return
    end if
    q = exp(-abs((energy-mu)/kt))
    weight = q/(kt*(1.0_real64+q)**2)
  end function

  function fs_weight_c(energy, mu, kt) result(weight) bind(C, name='fs_weight')
    real(c_double), value, intent(in) :: energy, mu, kt
    real(c_double) :: weight
    weight = fermi_weight(energy, mu, kt)
  end function

  subroutine accumulate_softness(rho, energy, mu, kt, kweight, degeneracy, &
                                 cutoff, softness, status)
    ! rho must already be in Angstrom^-3 and must include whatever PAW
    ! representation the caller intends. Never multiply by band occupation.
    real(real64), intent(in) :: rho(:), energy, mu, kt, kweight, degeneracy, cutoff
    real(real64), intent(inout) :: softness(:)
    integer, intent(out) :: status
    real(real64) :: weight
    status = 1
    if (size(rho) /= size(softness)) return
    if (.not. all(ieee_is_finite(rho))) return
    if (.not. all(ieee_is_finite(softness))) return
    if (.not. ieee_is_finite(kweight) .or. kweight < 0.0_real64) return
    if (.not. ieee_is_finite(degeneracy) .or. degeneracy <= 0.0_real64) return
    if (.not. ieee_is_finite(cutoff) .or. cutoff <= 0.0_real64) return
    weight = fermi_weight(energy, mu, kt)
    if (.not. ieee_is_finite(weight)) return
    if (cutoff >= 1.0_real64/(4.0_real64*kt)) return
    if (weight >= cutoff) softness = softness + kweight*degeneracy*weight*rho
    status = 0
  end subroutine
end module
