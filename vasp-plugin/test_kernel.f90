program test_kernel
  use, intrinsic :: iso_fortran_env, only: real64
  use fermi_softness_core
  implicit none
  real(real64) :: field(8), rho(8), total, energy, h
  integer :: status, i
  if (abs(fermi_weight(0.0_real64, 0.0_real64, 0.4_real64)-0.625_real64) > 1e-14_real64) stop 1
  ! Integrate the kernel numerically over +/- 40 kT.
  total=0.0_real64
  h=32.0_real64/32000
  do i=0,32000
    energy=-16.0_real64+i*h
    total=total+fermi_weight(energy,0.0_real64,0.4_real64)*h
  end do
  if (abs(total-1.0_real64)>1e-10_real64) stop 2
  rho=0.5_real64
  field=0.0_real64
  call accumulate_softness(rho,0.0_real64,0.0_real64,0.4_real64, &
                           0.25_real64,2.0_real64,0.001_real64,field,status)
  if (status/=0 .or. maxval(abs(field-0.15625_real64))>1e-14_real64) stop 3
  call accumulate_softness(rho,0.0_real64,0.0_real64,-1.0_real64, &
                           0.25_real64,2.0_real64,0.001_real64,field,status)
  if (status==0) stop 4
  print *, 'Fermi softness Fortran kernel: PASS'
end program
